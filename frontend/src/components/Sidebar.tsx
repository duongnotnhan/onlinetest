import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import {
  FiHome,
  FiUsers,
  FiFileText,
  FiAward,
  FiBarChart2,
  FiBook,
} from 'react-icons/fi'

export default function Sidebar() {
  const { user } = useAuthStore()
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  const adminLinks = [
    { path: '/admin/dashboard', label: 'Dashboard', icon: FiHome },
    { path: '/admin/teachers', label: 'Quản lý Giáo viên', icon: FiUsers },
    { path: '/admin/students', label: 'Quản lý Học sinh', icon: FiUsers },
    { path: '/admin/schools', label: 'Quản lý Trường', icon: FiBook },
    { path: '/admin/exams', label: 'Kỳ thi & Đề thi', icon: FiFileText },
    { path: '/admin/grading-assignments', label: 'Phân công chấm', icon: FiUsers },
    { path: '/admin/results', label: 'Kết quả thi', icon: FiBarChart2 },
  ]

  const teacherLinks = user?.teacher_type === 'NGU_VAN_GRADER' ? [
    { path: '/teacher/dashboard', label: 'Bảng Điều Khiển', icon: FiHome },
    { path: '/teacher/grade', label: 'Chấm Tự Luận', icon: FiAward },
  ] : [
    { path: '/teacher/dashboard', label: 'Bảng Điều Khiển', icon: FiHome },
    { path: '/teacher/students', label: 'Quản lý Thí sinh', icon: FiUsers },
    { path: '/teacher/results', label: 'Kết quả Trường', icon: FiBarChart2 },
  ]

  const studentLinks = [
    { path: '/student/dashboard', label: 'Dashboard', icon: FiHome },
  ]

  let links: Array<{ path: string; label: string; icon: any }> = []
  if (user?.role === 'admin') links = adminLinks
  else if (user?.role === 'teacher') links = teacherLinks
  else if (user?.role === 'student') links = studentLinks

  return (
    <div className="w-64 bg-white border-r border-gray-200 text-gray-700 flex flex-col shrink-0">
      <div className="p-5 border-b border-gray-100">
        <h2 className="text-lg font-bold text-gray-900 tracking-tight">Hệ Thống Thi Trực Tuyến</h2>
      </div>
      <nav className="mt-4 flex-1 overflow-y-auto space-y-0.5 px-2">
        {links.map(({ path, label, icon: Icon }) => {
          const active = isActive(path)
          return (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon size={18} className={active ? 'text-blue-600' : 'text-gray-400'} />
              <span>{label}</span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}