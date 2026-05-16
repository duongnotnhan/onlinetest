import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authAPI } from '@/api'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  
  const [formData, setFormData] = useState({
    cccd: '',
    password: '',
  })
  
  // Quản lý 6 ô mã OTP
  const [otp, setOtp] = useState<string[]>(new Array(6).fill(""))
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  const [loading, setLoading] = useState(false)
  const [loginType, setLoginType] = useState<'student' | 'teacher' | 'admin'>('student')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  // Xử lý khi nhập từng ô OTP
  const handleOtpChange = (element: HTMLInputElement, index: number) => {
    const value = element.value.replace(/[^0-9]/g, "") // Chỉ cho phép số
    if (!value && element.value !== "") return

    const newOtp = [...otp]
    newOtp[index] = value.substring(value.length - 1)
    setOtp(newOtp)

    // Tự động nhảy sang ô tiếp theo
    if (newOtp[index] && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  // Xử lý phím Backspace (xóa ngược)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  // Xử lý khi Paste (Dán) mã vào
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const data = e.clipboardData.getData("text").slice(0, 6).split("")
    if (data.every(char => /[0-9]/.test(char))) {
      const newOtp = [...otp]
      data.forEach((char, index) => {
        if (index < 6) newOtp[index] = char
      })
      setOtp(newOtp)
      inputRefs.current[Math.min(data.length, 5)]?.focus()
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    const fullTwoFaCode = otp.join("") // Kết hợp 6 ô thành chuỗi mã

    try {
      const response = await authAPI.login(
        formData.cccd, 
        formData.password, 
        loginType, 
        fullTwoFaCode
      )

      if (response.data.requires_2fa) {
        toast.error('Vui lòng nhập mã 6 số từ ứng dụng Xác thực (Authenticator)')
        return
      }

      const { user, access_token, refresh_token, requires_password_change, requires_2fa_setup } = response.data
      login(user, access_token, refresh_token)

      if (requires_password_change || user.is_first_login) {
        navigate('/change-password')
      } else if (requires_2fa_setup || (!user.two_fa_enabled && loginType !== 'student')) {
        navigate('/setup-2fa')
      } else {
        if (user.role === 'admin') navigate('/admin/dashboard')
        else if (user.role === 'teacher') navigate('/teacher/dashboard')
        else navigate('/student/dashboard')
      }

      toast.success('Đăng nhập thành công!')
    } catch (error: any) {
      // Xử lý lỗi mà không làm reload trang
      const errorMessage = error.response?.data?.error || 'Đăng nhập thất bại. Vui lòng kiểm tra lại.'
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-2">
          Hệ Thống Thi THPT
        </h1>
        <p className="text-center text-gray-500 mb-8">
          Kỳ thi tốt nghiệp THPT Quốc Gia
        </p>

        {/* Chế độ đăng nhập */}
        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setLoginType('student')}
            className={`flex-1 py-2 rounded transition-colors ${
              loginType === 'student' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Thí sinh
          </button>
          <button
            type="button"
            onClick={() => setLoginType('teacher')}
            className={`flex-1 py-2 rounded transition-colors ${
              loginType === 'teacher' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            GVQL/QTV
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Tài khoản / CCCD */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {loginType === 'student' ? 'Số CCCD/CMND/ĐDCN' : 'Tài khoản'}
            </label>
            <input
              type={loginType === 'student' ? "number" : "text"}
              name="cccd"
              value={formData.cccd}
              onChange={handleChange}
              required
              className="input-field w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder={loginType === 'student' ? "Nhập số định danh" : "Nhập tên đăng nhập"}
            />
          </div>

          {/* OTP Section (Mã Authenticator) */}
          {loginType !== 'student' && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Mã Authenticator (6 chữ số)
              </label>
              <div className="flex justify-between gap-2" onPaste={handlePaste}>
                {otp.map((data, index) => (
                  <input
                    key={index}
                    type="text"
                    ref={(el) => (inputRefs.current[index] = el)}
                    value={data}
                    onChange={(e) => handleOtpChange(e.target, index)}
                    onKeyDown={(e) => handleKeyDown(e, index)}
                    className="w-full h-12 text-center text-xl font-bold border-2 rounded-lg focus:border-blue-600 focus:ring-0 outline-none transition-all"
                    maxLength={1}
                    inputMode="numeric"
                    autoComplete="one-time-code" // Ngăn trình duyệt lưu/gợi ý mật khẩu cũ
                  />
                ))}
              </div>
              <p className="text-[10px] text-gray-400 italic text-center">
                Để trống nếu bạn thiết lập lần đầu
              </p>
            </div>
          )}

          {/* Mật khẩu */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mật khẩu
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="input-field w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="Nhập mật khẩu"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-4"
          >
            {loading ? 'Đang xác thực...' : 'Đăng nhập'}
          </button>
        </form>

        <p className="text-center text-gray-400 text-xs mt-8">
          © 2026 - Hệ Thống Thi Tốt Nghiệp THPT Quốc Gia
        </p>
      </div>
    </div>
  )
}