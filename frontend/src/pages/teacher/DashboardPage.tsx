import { useState, useEffect } from "react";
import { teacherAPI } from "@/api";
import toast from "react-hot-toast";
import { FiCalendar, FiUsers, FiAward, FiFileText } from "react-icons/fi";

export default function TeacherDashboard() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await teacherAPI.getDashboard();
        setDashboard(response.data);
      } catch (error) {
        toast.error("Lỗi tải dữ liệu bảng điều khiển: " + (error as Error).message);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-8 text-sm font-medium text-gray-500">
        Đang tải dữ liệu...
      </div>
    );
  }

  // Phân luồng hiển thị cho Giáo viên phụ trách chấm thi
  if (dashboard?.role_type === "grader") {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-bold text-gray-900">
          Bảng Điều Khiển Chấm Thi
        </h1>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="card flex justify-between items-center">
            <div>
              <p className="text-gray-500 text-xs font-medium">
                Tổng bài được giao
              </p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {dashboard.stats.total_assigned}
              </p>
            </div>
            <div className="p-2.5 bg-blue-50 text-blue-600 rounded-md">
              <FiFileText size={20} />
            </div>
          </div>
          <div className="card flex justify-between items-center">
            <div>
              <p className="text-gray-500 text-xs font-medium">
                Đã hoàn tất chấm
              </p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                {dashboard.stats.graded}
              </p>
            </div>
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-md">
              <FiAward size={20} />
            </div>
          </div>
          <div className="card flex justify-between items-center">
            <div>
              <p className="text-gray-500 text-xs font-medium">
                Đang chờ xử lý
              </p>
              <p className="text-2xl font-bold text-amber-600 mt-1">
                {dashboard.stats.pending}
              </p>
            </div>
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-md">
              <FiCalendar size={20} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Phân luồng hiển thị cho Giáo viên Quản lý khối/trường
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-900">
        Bảng Điều Khiển Quản Lý
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card flex justify-between items-center">
          <div>
            <p className="text-gray-500 text-xs font-medium">
              Học sinh trực thuộc
            </p>
            <p className="text-2xl font-bold text-blue-600 mt-1">
              {dashboard?.stats.total_students || 0}
            </p>
          </div>
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-md">
            <FiUsers size={20} />
          </div>
        </div>
        <div className="card flex justify-between items-center">
          <div>
            <p className="text-gray-500 text-xs font-medium">
              Thi dự phòng chờ duyệt
            </p>
            <p className="text-2xl font-bold text-amber-600 mt-1">
              {dashboard?.stats.pending_makeups || 0}
            </p>
          </div>
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-md">
            <FiCalendar size={20} />
          </div>
        </div>
        <div className="card flex justify-between items-center">
          <div>
            <p className="text-gray-500 text-xs font-medium">
              Kỳ thi đang kích hoạt
            </p>
            <p className="text-2xl font-bold text-indigo-600 mt-1">
              {dashboard?.stats.active_sessions || 0}
            </p>
          </div>
          <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-md">
            <FiFileText size={20} />
          </div>
        </div>
      </div>
    </div>
  );
}
