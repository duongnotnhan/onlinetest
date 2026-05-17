import React, { useState, useEffect } from "react";
import { adminAPI } from "@/api";
import toast from "react-hot-toast";

interface Student {
  student_id: number;
  full_name: string;
  cccd: string;
  school_name: string;
  is_active: boolean;
}

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await adminAPI.getStudents();
      setStudents(response.data.data || []);
    } catch (error) {
      toast.error("Lỗi khi tải danh sách học sinh");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Đang tải...</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Quản Lý Học Sinh
      </h1>

      <div className="card">
        <div className="mb-4 flex justify-between items-center">
          <p className="text-gray-600">
            Tổng cộng: <strong>{students.length}</strong> học sinh
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-3 px-4">Tên</th>
                <th className="text-left py-3 px-4">Mã định danh</th>
                <th className="text-left py-3 px-4">Trường</th>
                <th className="text-left py-3 px-4">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr
                  key={student.student_id}
                  className="border-b hover:bg-gray-50"
                >
                  <td className="py-3 px-4">{student.full_name}</td>
                  <td className="py-3 px-4">{student.cccd}</td>
                  <td className="py-3 px-4">{student.school_name}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        student.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {student.is_active ? "Hoạt động" : "Vô hiệu"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
