import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { adminAPI } from "@/api";
import { FiCheckCircle, FiPlus, FiXCircle } from "react-icons/fi";

interface Teacher {
  teacher_id: number;
  full_name: string;
  username: string;
  email: string;
  phone: string;
  school_id: number;
  school_name: string;
  subject_specialty: string;
  approval_status: string;
}

interface School {
  school_id: number;
  school_name: string;
  display_name?: string;
}

const teacherTypes = [
  { value: "GVQL", label: "Giáo viên quản trị trường" },
  { value: "NGU_VAN_GRADER", label: "Giáo viên chấm thi Ngữ văn" },
];

export default function TeachersManagementPage() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    email: "",
    phone: "",
    school_id: "",
    subject_specialty: "GVQL",
    temporary_password: "",
  });

  const fetchData = async () => {
    try {
      const [teachersResponse, schoolsResponse] = await Promise.all([
        adminAPI.getTeachers(),
        adminAPI.getSchools(),
      ]);
      setTeachers(teachersResponse.data.data || []);
      setSchools(schoolsResponse.data.data || []);
    } catch (error: any) {
      toast.error(
        error.response?.data?.error || "Không thể tải dữ liệu giáo viên",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const createTeacher = async (event: React.FormEvent) => {
    event.preventDefault();
    setCreating(true);
    try {
      const response = await adminAPI.createTeacher({
        ...form,
        school_id: Number(form.school_id),
        qualification_level:
          form.subject_specialty === "NGU_VAN_GRADER"
            ? "grader"
            : "school_admin",
      });
      toast.success(
        `Đã tạo tài khoản. Mật khẩu: ${response.data.temporary_password}`,
      );
      setForm({
        username: "",
        full_name: "",
        email: "",
        phone: "",
        school_id: "",
        subject_specialty: "GVQL",
        temporary_password: "",
      });
      fetchData();
    } catch (error: any) {
      toast.error(
        error.response?.data?.error || "Không thể tạo tài khoản giáo viên",
      );
    } finally {
      setCreating(false);
    }
  };

  const handleApprove = async (teacherId: number) => {
    try {
      await adminAPI.approveTeacher(teacherId);
      toast.success("Đã duyệt giáo viên");
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Lỗi khi duyệt giáo viên");
    }
  };

  const handleReject = async (teacherId: number) => {
    const reason = prompt("Nhập lý do từ chối:");
    if (!reason) return;
    try {
      await adminAPI.rejectTeacher(teacherId, reason);
      toast.success("Đã từ chối giáo viên");
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Lỗi khi từ chối giáo viên");
    }
  };

  if (loading) return <div className="text-center py-8">Đang tải...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Quản Lý Giáo Viên</h1>
        <p className="text-gray-500 mt-1">
          Tạo tài khoản GVQL của trường và giáo viên chấm thi Ngữ văn.
        </p>
      </div>

      <form onSubmit={createTeacher} className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <FiPlus /> Tạo tài khoản giáo viên
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            className="input-field"
            placeholder="Tài khoản"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            className="input-field"
            placeholder="Họ và tên"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            required
          />
          <input
            className="input-field"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            className="input-field"
            placeholder="SĐT"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
          <select
            title="chooseSchool"
            className="input-field"
            value={form.school_id}
            onChange={(e) => setForm({ ...form, school_id: e.target.value })}
            required
          >
            <option value="">Chọn trường</option>
            {schools.map((school) => (
              <option key={school.school_id} value={school.school_id}>
                {school.display_name || school.school_name}
              </option>
            ))}
          </select>
          <select
            title="chooseTeacherRole"
            className="input-field"
            value={form.subject_specialty}
            onChange={(e) =>
              setForm({ ...form, subject_specialty: e.target.value })
            }
          >
            {teacherTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <input
            className="input-field md:col-span-2"
            placeholder="Mật khẩu tạm thời (bỏ trống để tự sinh)"
            value={form.temporary_password}
            onChange={(e) =>
              setForm({ ...form, temporary_password: e.target.value })
            }
          />
          <button
            className="btn-primary disabled:opacity-50"
            disabled={creating}
          >
            {creating ? "Đang tạo..." : "Tạo tài khoản"}
          </button>
        </div>
      </form>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-3 px-4">Giáo viên</th>
                <th className="text-left py-3 px-4">Tài khoản</th>
                <th className="text-left py-3 px-4">Trường</th>
                <th className="text-left py-3 px-4">Vai trò</th>
                <th className="text-left py-3 px-4">Trạng thái</th>
                <th className="text-left py-3 px-4">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {teachers.map((teacher) => (
                <tr
                  key={teacher.teacher_id}
                  className="border-b hover:bg-gray-50"
                >
                  <td className="py-3 px-4">
                    <div className="font-medium">{teacher.full_name}</div>
                    <div className="text-xs text-gray-500">
                      {teacher.email || teacher.phone}
                    </div>
                  </td>
                  <td className="py-3 px-4">{teacher.username}</td>
                  <td className="py-3 px-4">{teacher.school_name}</td>
                  <td className="py-3 px-4">
                    {teacher.subject_specialty === "NGU_VAN_GRADER"
                      ? "Chấm Ngữ văn"
                      : "GVQL trường"}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${teacher.approval_status === "approved" ? "bg-green-100 text-green-700" : teacher.approval_status === "pending" ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"}`}
                    >
                      {teacher.approval_status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    {teacher.approval_status === "pending" && (
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleApprove(teacher.teacher_id)}
                          className="text-green-600 hover:underline flex items-center gap-1"
                        >
                          <FiCheckCircle /> Duyệt
                        </button>
                        <button
                          onClick={() => handleReject(teacher.teacher_id)}
                          className="text-red-600 hover:underline flex items-center gap-1"
                        >
                          <FiXCircle /> Từ chối
                        </button>
                      </div>
                    )}
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
