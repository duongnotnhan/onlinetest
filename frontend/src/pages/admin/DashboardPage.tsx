import { useState, useEffect } from 'react'
import { adminAPI } from '@/api'
import toast from 'react-hot-toast'
import { FiUsers, FiBook, FiFileText, FiCheckCircle } from 'react-icons/fi'

interface DashboardStats {
  total_teachers: number
  pending_teachers: number
  total_schools: number
  total_students: number
  active_sessions: number
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await adminAPI.getDashboard()
        setStats(response.data)
      } catch (error) {
        toast.error('Lỗi khi tải dữ liệu tổng quan')
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [])

  if (loading) {
    return <div className="text-center py-8 text-sm font-medium text-gray-500">Đang tải dữ liệu...</div>
  }

  const statCards = [
    {
      title: 'Tổng Giáo viên',
      value: stats?.total_teachers || 0,
      icon: FiUsers,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      title: 'Chờ Duyệt',
      value: stats?.pending_teachers || 0,
      icon: FiCheckCircle,
      color: 'bg-amber-50 text-amber-600',
    },
    {
      title: 'Trường Học',
      value: stats?.total_schools || 0,
      icon: FiBook,
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      title: 'Học sinh',
      value: stats?.total_students || 0,
      icon: FiUsers,
      color: 'bg-indigo-50 text-indigo-600',
    },
    {
      title: 'Kỳ Thi Đang Mở',
      value: stats?.active_sessions || 0,
      icon: FiFileText,
      color: 'bg-rose-50 text-rose-600',
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-900">
        Tổng Quan Hệ Thống
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((card, index) => {
          const Icon = card.icon
          return (
            <div key={index} className="card flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-xs font-medium">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {card.value}
                </p>
              </div>
              <div className={`p-2.5 rounded-md ${card.color}`}>
                <Icon size={20} />
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-base font-bold text-gray-900 mb-3 border-b border-gray-100 pb-2">
            Hoạt Động Gần Đây
          </h2>
          <p className="text-gray-500 text-sm italic">Chưa có dữ liệu giao dịch phát sinh.</p>
        </div>

        <div className="card">
          <h2 className="text-base font-bold text-gray-900 mb-3 border-b border-gray-100 pb-2">
            Trạng Thái Dịch Vụ
          </h2>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Hệ thống lõi hoạt động ổn định
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Đồng bộ hóa cơ sở dữ liệu thành công
            </li>
            <li className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
              Băng thông đường truyền bình thường
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}