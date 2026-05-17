import React from 'react'
import { useAuthStore } from '@/store/authStore'
import { FiLogOut, FiSettings } from 'react-icons/fi'

export default function Navbar() {
  const { user, logout } = useAuthStore()

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {user?.role === 'admin' ? 'Bảng Điều Khiển Quản Trị Viên' : user?.role === 'teacher' ? 'Bảng Điều Khiển Giáo Viên' : 'Bảng Điều Khiển Thí Sinh'}
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-700">
            {user?.full_name} ({user?.role === 'admin' ? 'Quản trị viên' : user?.role === 'teacher' ? 'Giáo viên' : 'Thí sinh'})
          </span>
          <button
            onClick={logout}
            className="p-2 hover:bg-gray-100 rounded-lg text-red-600"
            title="Logout"
          >
            <FiLogOut size={20} />
          </button>
        </div>
      </div>
    </nav>
  )
}
