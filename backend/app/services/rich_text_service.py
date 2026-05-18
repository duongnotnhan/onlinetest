"""Rich Text và Media Management Service"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from html import escape
import bleach  # Để sanitize HTML
from app import db
from app.models import (MediaUploadLog, QuestionComment,
                        QuestionMedia, RichTextTemplate)


class RichTextService:
    """Service cho Rich Text Formatting"""

    # Các HTML tag được phép sử dụng
    ALLOWED_TAGS = {
        "p",
        "br",
        "strong",
        "em",
        "u",
        "span",
        "div",
        "b",
        "i",
        "sub",
        "sup",
        "mark",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "blockquote",
        "pre",
        "code",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "img",
        "video",
        "audio",
        "figure",
        "figcaption",
    }

    # Các attribute được phép sử dụng
    ALLOWED_ATTRIBUTES = {
        "*": ["class", "id", "style", "title", "alt"],
        "img": ["src", "alt", "width", "height", "data-*"],
        "a": ["href", "target", "rel"],
        "video": ["src", "width", "height", "controls", "poster"],
        "audio": ["src", "controls"],
        "span": ["class", "style", "data-*"],
        "p": ["style", "align"],
    }

    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """
        Sanitize HTML content để bảo vệ khỏi XSS attacks

        Args:
            html_content: HTML content cần sanitize

        Returns:
            Sanitized HTML content
        """
        if not html_content:
            return ""

        return bleach.clean(
            html_content,
            tags=RichTextService.ALLOWED_TAGS,
            attributes=RichTextService.ALLOWED_ATTRIBUTES,
            strip=True,
        )

    @staticmethod
    def convert_to_rich_text_format(plain_text: str) -> str:
        """
        Chuyển đổi plain text sang rich text format (HTML)

        Args:
            plain_text: Plain text content

        Returns:
            HTML formatted content
        """
        if not plain_text:
            return ""

        # Escape HTML special characters trước
        escaped = escape(plain_text)

        # Chuyển newline thành <br>
        html = escaped.replace("\n", "<br>")

        # Wrap trong <p> tag
        html = f"<p>{html}</p>"

        return html

    @staticmethod
    def create_rich_text_template(
        template_name: str,
        template_code: str,
        html_content: str,
        category: str = None,
        preview_text: str = None,
        created_by: int = None,
    ) -> Optional[RichTextTemplate]:
        """
        Tạo một rich text template

        Args:
            template_name: Tên template
            template_code: Mã code duy nhất của template
            html_content: Nội dung HTML của template
            category: Danh mục template
            preview_text: Text preview
            created_by: User ID tạo template

        Returns:
            RichTextTemplate object hoặc None nếu lỗi
        """
        try:
            # Sanitize HTML content
            sanitized_html = RichTextService.sanitize_html(html_content)

            template = RichTextTemplate(
                template_name=template_name,
                template_code=template_code,
                html_content=sanitized_html,
                category=category,
                preview_text=preview_text,
                created_by=created_by,
            )

            db.session.add(template)
            db.session.commit()

            return template

        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error adding comment: {str(e)}') from e

    @staticmethod
    def get_templates_by_category(category: str) -> List[RichTextTemplate]:
        """
        Lấy các template theo danh mục

        Args:
            category: Danh mục template

        Returns:
            List của RichTextTemplate objects
        """
        return RichTextTemplate.query.filter_by(
            category=category, is_active=True).all()

    @staticmethod
    def apply_template(
            template_code: str,
            replacements: Dict = None) -> Optional[str]:
        """
        Áp dụng template với thay thế variables

        Args:
            template_code: Mã code của template
            replacements: Dict của các variable cần thay thế

        Returns:
            HTML content sau khi áp dụng template
        """
        template = RichTextTemplate.query.filter_by(
            template_code=template_code, is_active=True
        ).first()

        if not template:
            return None

        html_content = template.html_content

        if replacements:
            for key, value in replacements.items():
                placeholder = f"{{{{{key}}}}}"
                html_content = html_content.replace(placeholder, str(value))

        return html_content


class MediaService:
    """Service cho Media/Image Management"""

    # Các MIME type được phép upload
    ALLOWED_MIME_TYPES = {
        "image": [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4"],
        "video": ["video/mp4", "video/webm", "video/ogg"],
        "document": ["application/pdf", "application/msword"],
    }

    # Giới hạn kích thước file (theo byte)
    MAX_FILE_SIZE = {
        "image": 5 * 1024 * 1024,  # 5MB
        "audio": 20 * 1024 * 1024,  # 20MB
        "video": 100 * 1024 * 1024,  # 100MB
        "document": 10 * 1024 * 1024,  # 10MB
    }

    @staticmethod
    def upload_media(
        file,
        media_type: str,
        question_id: int = None,
        section_id: int = None,
        passage_id: int = None,
        alt_text: str = None,
        caption: str = None,
        created_by: int = None,
        upload_dir: str = "uploads/media",
    ) -> Tuple[bool, str, Optional[QuestionMedia]]:
        """
        Upload media file

        Args:
            file: File object từ request
            media_type: Loại media ('image', 'audio', 'video', 'document')
            question_id: ID của câu hỏi (optional)
            section_id: ID của phần (optional)
            passage_id: ID của passage (optional)
            alt_text: Alternative text cho image
            caption: Caption của media
            created_by: User ID upload
            upload_dir: Thư mục upload

        Returns:
            Tuple (success: bool, message: str, media: QuestionMedia or None)
        """
        try:
            if not file or file.filename == "":
                return False, "Không có file được chọn", None

            # Validate file size
            file_size = len(file.read())
            file.seek(0)  # Reset file pointer

            if file_size > MediaService.MAX_FILE_SIZE.get(
                    media_type, 5 * 1024 * 1024):
                return False, f"File quá lớn. Max size: {
                    MediaService.MAX_FILE_SIZE.get(media_type)}", None

            # Validate MIME type
            mime_type = file.content_type
            if mime_type not in MediaService.ALLOWED_MIME_TYPES.get(
                    media_type, []):
                return False, f"Loại file không được hỗ trợ: {mime_type}", None

            # Tạo tên file với timestamp
            original_filename = file.filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
            stored_filename = timestamp + original_filename

            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(upload_dir, exist_ok=True)

            # Lưu file
            file_path = os.path.join(upload_dir, stored_filename)
            file.save(file_path)

            # Tạo QuestionMedia record
            media = QuestionMedia(
                question_id=question_id,
                section_id=section_id,
                passage_id=passage_id,
                media_type=media_type,
                media_filename=original_filename,
                media_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                alt_text=alt_text,
                caption=caption,
                created_by=created_by,
            )

            db.session.add(media)
            db.session.commit()

            # Tạo upload log
            upload_log = MediaUploadLog(
                media_id=media.media_id,
                upload_by=created_by,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
            )

            db.session.add(upload_log)
            db.session.commit()

            return True, "Upload media thành công", media

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi upload media: {str(e)}", None

    @staticmethod
    def get_media(media_id: int) -> Optional[QuestionMedia]:
        """Lấy media theo ID"""
        return QuestionMedia.query.get(media_id)

    @staticmethod
    def delete_media(media_id: int) -> Tuple[bool, str]:
        """
        Xóa media

        Args:
            media_id: ID của media cần xóa

        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            media = QuestionMedia.query.get(media_id)

            if not media:
                return False, "Media không tồn tại"

            # Xóa file vật lý
            if os.path.exists(media.media_path):
                os.remove(media.media_path)

            # Xóa từ database
            db.session.delete(media)
            db.session.commit()

            return True, "Xóa media thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi xóa media: {str(e)}"

    @staticmethod
    def get_media_by_question(question_id: int) -> List[QuestionMedia]:
        """Lấy tất cả media của một câu hỏi"""
        return QuestionMedia.query.filter_by(question_id=question_id).all()

    @staticmethod
    def get_media_by_section(section_id: int) -> List[QuestionMedia]:
        """Lấy tất cả media của một phần"""
        return QuestionMedia.query.filter_by(section_id=section_id).all()

    @staticmethod
    def get_media_by_passage(passage_id: int) -> List[QuestionMedia]:
        """Lấy tất cả media của một passage"""
        return QuestionMedia.query.filter_by(passage_id=passage_id).all()


class QuestionCommentService:
    """Service cho Question Comments"""

    @staticmethod
    def add_comment(
        question_id: int, comment_text: str, created_by: int
    ) -> Optional[QuestionComment]:
        """
        Thêm bình luận cho câu hỏi

        Args:
            question_id: ID của câu hỏi
            comment_text: Nội dung bình luận
            created_by: User ID tạo bình luận

        Returns:
            QuestionComment object hoặc None nếu lỗi
        """
        try:
            comment = QuestionComment(
                question_id=question_id,
                comment_text=comment_text,
                created_by=created_by,
            )

            db.session.add(comment)
            db.session.commit()

            return comment

        except Exception as e:
            db.session.rollback()
            raise Exception(f'Error adding comment: {str(e)}') from e

    @staticmethod
    def get_comments(question_id: int) -> List[QuestionComment]:
        """Lấy tất cả bình luận của một câu hỏi"""
        return (
            QuestionComment.query.filter_by(question_id=question_id)
            .order_by(QuestionComment.created_at.desc())
            .all()
        )

    @staticmethod
    def delete_comment(comment_id: int) -> Tuple[bool, str]:
        """Xóa bình luận"""
        try:
            comment = QuestionComment.query.get(comment_id)

            if not comment:
                return False, "Bình luận không tồn tại"

            db.session.delete(comment)
            db.session.commit()

            return True, "Xóa bình luận thành công"

        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi xóa bình luận: {str(e)}"


# ============================================================
# RICH TEXT TEMPLATE EXAMPLES
# ============================================================
DEFAULT_RICH_TEXT_TEMPLATES = [{"template_name": "Tiêu đề Chính",
                                "template_code": "title_main",
                                "html_content": '<h1 style="text-align: center; \
                                    color: #000; font-weight: bold;">{title}</h1>',
                                "category": "headings",
                                "preview_text": "Tiêu đề lớn căn giữa",
                                },
                               {"template_name": "Tiêu đề Phụ",
                                "template_code": "title_sub",
                                "html_content": '<h2 style="color: #333;">{subtitle}</h2>',
                                "category": "headings",
                                "preview_text": "Tiêu đề cỡ trung",
                                },
                               {"template_name": "Đoạn Văn Thường",
                                "template_code": "paragraph_normal",
                                "html_content": '<p style="line-height: 1.6; \
                                    text-align: justify;">{content}</p>',
                                "category": "paragraphs",
                                "preview_text": "Đoạn văn căn hai lề",
                                },
                               {"template_name": "Văn Bản Nhấn Mạnh",
                                "template_code": "text_highlight",
                                "html_content": '<p><strong><mark style="background-color: \
                                    yellow;">{text}</mark></strong></p>',
                                "category": "text_formatting",
                                "preview_text": "Text in đậm và highlight màu vàng",
                                },
                               {"template_name": "Danh Sách Đạn",
                                "template_code": "list_bullet",
                                "html_content": "<ul><li>{item1}</li><li>{item2}</li>\
                                    <li>{item3}</li></ul>",
                                "category": "lists",
                                "preview_text": "Danh sách có dấu chấm",
                                },
                               {"template_name": "Danh Sách Số",
                                "template_code": "list_numbered",
                                "html_content": "<ol><li>{item1}</li><li>{item2}</li>\
                                    <li>{item3}</li></ol>",
                                "category": "lists",
                                "preview_text": "Danh sách đánh số",
                                },
                               {"template_name": "Trích Dẫn",
                                "template_code": "blockquote",
                                "html_content": '<blockquote style="border-left: 4px solid #ccc; \
                                padding-left: 15px; margin: 15px 0; font-style: italic; color: \
                                    #666;">{quote}</blockquote>',
                                "category": "text_formatting",
                                "preview_text": "Đoạn trích dẫn",
                                },
                               {"template_name": "Bảng Đơn Giản",
                                "template_code": "table_simple",
                                "html_content": '<table style="border-collapse: collapse; \
                                    width: 100%;">\
                                    <thead><tr style="background-color: #f0f0f0;"><th style="border: \
                                    1px solid #ccc; padding: 10px;">{header1}</th><th style="border: \
                                    1px solid #ccc; padding: 10px;">{header2}</th></tr></thead><tbody>\
                                    <tr><td style="border: 1px solid #ccc; padding: 10px;">{cell1}</td>\
                                    <td style="border: 1px solid #ccc; padding: 10px;">{cell2}</td></tr>\
                                    </tbody></table>',
                                "category": "tables",
                                "preview_text": "Bảng cơ bản",
                                },
                               ]


def initialize_default_templates(created_by: int = 1):
    """Khởi tạo các template mặc định"""
    for template_data in DEFAULT_RICH_TEXT_TEMPLATES:
        existing = RichTextTemplate.query.filter_by(
            template_code=template_data["template_code"]
        ).first()

        if not existing:
            template = RichTextTemplate(
                template_name=template_data["template_name"],
                template_code=template_data["template_code"],
                html_content=template_data["html_content"],
                category=template_data["category"],
                preview_text=template_data["preview_text"],
                created_by=created_by,
            )

            db.session.add(template)

    db.session.commit()
