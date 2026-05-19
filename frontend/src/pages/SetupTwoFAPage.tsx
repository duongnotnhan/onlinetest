import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { authAPI } from "@/api";
import { useAuthStore } from "@/store/authStore";

export default function SetupTwoFAPage() {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const [secret, setSecret] = useState("");
  const [qrCode, setQrCode] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    authAPI
      .setupTwoFA()
      .then((response) => {
        setSecret(response.data.secret);
        setQrCode(response.data.qr_code);
      })
      .catch((error) =>
        toast.error(error.response?.data?.error || "Không thể tạo mã 2FA"),
      );
  }, []);

  const goHome = () => {
    if (user?.role === "admin") navigate("/admin/dashboard");
    else navigate("/teacher/dashboard");
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await authAPI.verifyTwoFA(secret, otp);
      if (user) {
        setUser({ ...user, two_fa_enabled: true, is_first_login: false });
      }
      toast.success("Đã bật xác thực 2 lớp");
      goHome();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Mã xác thực không hợp lệ");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="card w-full max-w-md space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Liên kết Authenticator
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Quét QR bằng Google Authenticator, Microsoft Authenticator hoặc ứng
            dụng tương thích.
          </p>
        </div>
        {qrCode && (
          <img src={qrCode} alt="Mã QR 2FA" className="mx-auto h-48 w-48" />
        )}
        <div className="text-xs text-gray-500 break-all">Secret: {secret}</div>
        <input
          className="input-field text-center tracking-widest"
          value={otp}
          onChange={(event) => setOtp(event.target.value)}
          inputMode="numeric"
          maxLength={6}
          placeholder="Nhập mã xác thực 6 chữ số"
          required
        />
        <button
          className="btn-primary w-full disabled:opacity-50"
          disabled={loading || !secret}
        >
          {loading ? "Đang xác nhận..." : "Xác nhận"}
        </button>
      </form>
    </div>
  );
}
