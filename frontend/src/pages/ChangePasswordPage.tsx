import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { authAPI } from "@/api";
import { useAuthStore } from "@/store/authStore";

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const goHome = (role?: string) => {
    if (role === "admin") navigate("/admin/dashboard");
    else if (role === "teacher") navigate("/teacher/dashboard");
    else navigate("/student/dashboard");
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error("Mật khẩu xác nhận chưa khớp");
      return;
    }

    setLoading(true);
    try {
      const response = await authAPI.firstLoginChangePassword(
        oldPassword,
        newPassword,
      );
      if (user) {
        setUser({ ...user, is_first_login: false });
      }
      toast.success("Đổi mật khẩu thành công");
      if (response.data.requires_2fa_setup) navigate("/setup-2fa");
      else goHome(user?.role);
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Không thể đổi mật khẩu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="card w-full max-w-md space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Đổi mật khẩu lần đầu
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Mật khẩu mới tối thiểu 8 ký tự, có số và ký tự đặc biệt.
          </p>
        </div>
        <input
          className="input-field"
          type="password"
          placeholder="Mật khẩu hiện tại"
          value={oldPassword}
          onChange={(event) => setOldPassword(event.target.value)}
          required
        />
        <input
          className="input-field"
          type="password"
          placeholder="Mật khẩu mới"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          required
        />
        <input
          className="input-field"
          type="password"
          placeholder="Xác nhận mật khẩu mới"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          required
        />
        <button
          className="btn-primary w-full disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Đang lưu..." : "Lưu mật khẩu"}
        </button>
      </form>
    </div>
  );
}
