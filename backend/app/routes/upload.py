"""File upload utilities and API endpoints"""

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pathlib import Path
import uuid
from PIL import Image
import io
from . import upload_bp

# Allowed extensions and size limits
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
THUMBNAIL_SIZE = (300, 200)
PREVIEW_SIZE = (800, 600)


def get_upload_folder():
    """Get upload folder path"""
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    return upload_dir


def compress_image(image_data, max_size=PREVIEW_SIZE):
    """Compress image to reduce file size"""
    try:
        img = Image.open(io.BytesIO(image_data))

        # Convert RGBA to RGB if necessary
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()
                             [-1] if img.mode == "RGBA" else None)
            img = background

        # Resize if needed
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save with optimization
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=85, method=6)
        return output.getvalue()
    except Exception as e:
        print(f"Error compressing image: {e}")
        return image_data


@upload_bp.route("/image", methods=["POST"])
@jwt_required()
def upload_image():
    """Upload image file"""
    try:
        user_id = get_jwt_identity()

        # Check if file is in request
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Validate file extension
        filename = secure_filename(file.filename)
        ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return (
                jsonify(
                    {
                        "error": f'File type not allowed. Allowed: {
                            ", ".join(ALLOWED_IMAGE_EXTENSIONS)}'}),
                400,
            )

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_IMAGE_SIZE:
            return (
                jsonify(
                    {
                        "error": f"File size exceeds {MAX_IMAGE_SIZE / (1024 * 1024):.0f}MB limit"
                    }
                ),
                400,
            )

        # Read file data
        file_data = file.read()

        # Compress image
        compressed_data = compress_image(file_data)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{timestamp}_{unique_id}.webp"

        # Create upload folder structure
        upload_folder = get_upload_folder()
        save_path = os.path.join(upload_folder, "images")
        Path(save_path).mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = os.path.join(save_path, new_filename)
        with open(file_path, "wb") as f:
            f.write(compressed_data)

        # Generate URL
        relative_url = f"/api/upload/images/{new_filename}"

        return (
            jsonify(
                {
                    "success": True,
                    "url": relative_url,
                    "filename": new_filename,
                    "original_filename": filename,
                    "file_size": file_size,
                    "compressed_size": len(compressed_data),
                    "message": "Image uploaded successfully",
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@upload_bp.route("/images/<path:filepath>", methods=["GET"])
def serve_image(filepath):
    """Serve uploaded image"""
    try:
        from flask import send_from_directory

        upload_folder = get_upload_folder()
        return send_from_directory(
            os.path.join(
                upload_folder,
                "images"),
            filepath)
    except Exception as e:
        return jsonify({"error": "Image not found"}), 404


@upload_bp.route("/image/<filename>", methods=["DELETE"])
@jwt_required()
def delete_image(filename):
    """Delete uploaded image"""
    try:
        user_id = get_jwt_identity()
        upload_folder = get_upload_folder()

        # Find and delete file (search in recent dates)
        import glob

        pattern = os.path.join(upload_folder, "images", filename)
        files = glob.glob(pattern, recursive=True)

        if not files:
            return jsonify({"error": "File not found"}), 404

        for file in files:
            os.remove(file)

        return jsonify(
            {"success": True, "message": "Image deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500


# Helper function to register blueprint in app
def init_upload_routes(app):
    """Initialize upload routes"""
    # Create uploads directory
    upload_dir = app.config.get("UPLOAD_FOLDER", "uploads")
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    # Register static files
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return upload_bp.send_static_file(filename)

    app.register_blueprint(upload_bp)
