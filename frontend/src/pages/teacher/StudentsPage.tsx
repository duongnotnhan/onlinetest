import React, { ReactNode, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { teacherAPI, exportAPI } from "@/api";
import {
  FiUpload,
  FiRefreshCw,
  FiXCircle,
  FiCheckCircle,
  FiAlertCircle,
  FiEdit,
  FiDownloadCloud,
} from "react-icons/fi";

interface Student {
  student_id: number;
  cccd: string;
  full_name: string;
  gender: string;
  date_of_birth: string;
  address: string;
  phone: string;
  class_name: string;
  is_active: boolean;
  elective_subject_1?: string;
  elective_subject_2?: string;
}

interface ImportResult {
  total: number;
  imported: number;
  failed: number;
  errors: {
    [x: string]: ReactNode; row: number; error: any 
}[];
}

// Danh sách các môn tự chọn (Dựa trên DB cung cấp)
const ELECTIVE_SUBJECTS = [
  { code: "VAT_LI", name: "Vật Lí" },
  { code: "HOA_HO", name: "Hóa Học" },
  { code: "SINH_H", name: "Sinh Học" },
  { code: "DIA_LI", name: "Địa Lí" },
  { code: "LICH_S", name: "Lịch Sử" },
  { code: "GDKTVL", name: "Giáo Dục KT & PL" },
  { code: "TIN_HO", name: "Tin Học" },
  { code: "CNNG", name: "Công Nghệ Công Nghiệp" },
  { code: "CNNN", name: "Công Nghệ Nông Nghiệp" },
  { code: "TIENG_ANH", name: "Tiếng Anh" },
  { code: "TIENG_RU", name: "Tiếng Nga" },
  { code: "TIENG_PH", name: "Tiếng Pháp" },
  { code: "TIENG_TR", name: "Tiếng Trung" },
  { code: "TIENG_DU", name: "Tiếng Đức" },
  { code: "TIENG_NH", name: "Tiếng Nhật" },
  { code: "TIENG_HAN", name: "Tiếng Hàn" },
  { code: "MT", name: "Miễn thi" },
];

export default function TeacherStudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  // States cho Import
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);

  // States cho Sửa thủ công
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [editForm, setEditForm] = useState<any>({});
  const [saving, setSaving] = useState(false);

  const fetchStudents = async () => {
    try {
      const response = await teacherAPI.getStudents();
      setStudents(response.data.data || []);
    } catch (error) {
      toast.error(
        "Không thể tải danh sách thí sinh: " + (error as Error).message,
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  // Xử lý Reset Mật khẩu
  const resetPassword = async (studentId: number) => {
    if (
      !confirm(
        "Bạn có chắc chắn muốn cấp lại mật khẩu tạm thời cho thí sinh này?",
      )
    )
      return;
    try {
      const response = await teacherAPI.resetStudentPassword(studentId);
      toast.success(`Mật khẩu mới: ${response.data.temporary_password}`, {
        duration: 6000,
      });
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Không thể reset mật khẩu");
    }
  };

  // Xử lý Import CSV
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setImportFile(e.target.files[0]);
      setImportResult(null);
    }
  };

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return toast.error("Vui lòng chọn file CSV");

    setImporting(true);
    setImportResult(null);
    try {
      const response = await teacherAPI.importStudents(importFile);
      setImportResult(response.data);
      if (response.data.failed === 0) {
        toast.success(`Nhập thành công ${response.data.imported} thí sinh!`);
        setTimeout(() => {
          setShowImportModal(false);
          setImportFile(null);
          setImportResult(null);
        }, 2000);
      } else {
        toast.error(
          `Nhập hoàn tất. Thành công: ${response.data.imported}, Lỗi: ${response.data.failed}`,
        );
      }
      fetchStudents();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Lỗi khi nhập dữ liệu");
    } finally {
      setImporting(false);
    }
  };

  // Xử lý Sửa học sinh
  const openEditModal = (student: Student) => {
    setEditingStudent(student);
    setEditForm({
      full_name: student.full_name,
      gender: student.gender,
      date_of_birth: student.date_of_birth,
      class_name: student.class_name,
      phone: student.phone || "",
      elective_subject_1: student.elective_subject_1 || "",
      elective_subject_2: student.elective_subject_2 || "",
    });
    setShowEditModal(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStudent) return;
    if (
      editForm.elective_subject_1 === editForm.elective_subject_2 &&
      editForm.elective_subject_1 !== ""
    ) {
      return toast.error("Hai môn tự chọn không được trùng nhau!");
    }

    setSaving(true);
    try {
      await teacherAPI.updateStudent(editingStudent.student_id, editForm);
      toast.success("Cập nhật thông tin thành công");
      setShowEditModal(false);
      fetchStudents();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Lỗi cập nhật");
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return <div className="text-center py-8">Đang tải dữ liệu hệ thống...</div>;

  return (
    <div className="space-y-6 text-left">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Quản Lý Thí Sinh</h1>
          <p className="text-gray-500 mt-1">
            Quản lý hồ sơ, cấp lại mật khẩu và nhập danh sách dự thi.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowImportModal(true)}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            <FiUpload /> Nhập file CSV
          </button>
          <button
            type="button"
            onClick={() => exportAPI.downloadTemplate("student")}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <FiDownloadCloud /> Tải mẫu CSV
          </button>
          <button
            onClick={() =>
              teacherAPI.resetBulkPasswords(students.map((s) => s.student_id))
            }
            className="btn-secondary flex items-center gap-2 text-sm bg-red-600 hover:bg-red-700 hover:text-white"
          >
            <FiRefreshCw size={18} /> Reset Toàn Bộ Mật Khẩu
          </button>
        </div>
      </div>

      <div className="card space-y-4 p-0 overflow-hidden">
        <div className="flex justify-between items-center border-b pb-4 bg-gray-900 text-white p-4">
          <h2 className="text-lg font-bold">Danh sách thí sinh trường</h2>
          <span className="bg-blue-600 px-3 py-1 rounded text-sm font-medium">
            {students.length} Thí sinh
          </span>
        </div>
        <div className="overflow-x-auto p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-gray-700">
                <th className="text-left py-3 px-4 font-bold uppercase tracking-wider text-xs">
                  Họ và tên
                </th>
                <th className="text-left py-3 px-4 font-bold uppercase tracking-wider text-xs">
                  Mã định danh
                </th>
                <th className="text-left py-3 px-4 font-bold uppercase tracking-wider text-xs">
                  Lớp
                </th>
                <th className="text-left py-3 px-4 font-bold uppercase tracking-wider text-xs">
                  Môn Tự Chọn
                </th>
                <th className="text-right py-3 px-4 font-bold uppercase tracking-wider text-xs">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr
                  key={student.student_id}
                  className="border-b hover:bg-gray-50 transition-colors"
                >
                  <td className="py-3 px-4 font-medium text-gray-900">
                    {student.full_name}
                  </td>
                  <td className="py-3 px-4 font-mono text-blue-600">
                    {student.cccd}
                  </td>
                  <td className="py-3 px-4">{student.class_name}</td>
                  <td className="py-3 px-4">
                    {student.elective_subject_1 ||
                    student.elective_subject_2 ? (
                      <div className="flex flex-col gap-1 text-xs">
                        <span className="bg-gray-100 px-2 py-1 rounded w-fit">
                          {ELECTIVE_SUBJECTS.find(
                            (s) => s.code === student.elective_subject_1,
                          )?.name || student.elective_subject_1}
                        </span>
                        <span className="bg-gray-100 px-2 py-1 rounded w-fit">
                          {ELECTIVE_SUBJECTS.find(
                            (s) => s.code === student.elective_subject_2,
                          )?.name || student.elective_subject_2}
                        </span>
                      </div>
                    ) : (
                      <span className="text-red-500 text-xs italic">
                        Chưa chọn môn
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 flex justify-end gap-2">
                    <button
                      type="button"
                      className="text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                      onClick={() => openEditModal(student)}
                    >
                      <FiEdit size={14} /> Sửa
                    </button>
                    <button
                      type="button"
                      className="text-orange-600 hover:text-orange-800 bg-orange-50 hover:bg-orange-100 px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                      onClick={() => resetPassword(student.student_id)}
                      title="Cấp lại mật khẩu mặc định"
                    >
                      <FiRefreshCw size={14} /> Reset Pass
                    </button>
                  </td>
                </tr>
              ))}
              {students.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-gray-500">
                    Trường chưa có thí sinh nào. Vui lòng nhập dữ liệu từ file
                    CSV.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- MODAL EDIT THỦ CÔNG --- */}
      {showEditModal && editingStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b bg-gray-50 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900">
                Sửa thông tin thí sinh
              </h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-gray-400 hover:text-red-500"
                aria-label="Close edit modal"
              >
                <FiXCircle size={24} />
              </button>
            </div>
            <form
              id="edit-form"
              onSubmit={handleSaveEdit}
              className="p-6 space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Họ và tên
                </label>
                <input
                  title="fullName"
                  className="input-field"
                  value={editForm.full_name}
                  onChange={(e) =>
                    setEditForm({ ...editForm, full_name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lớp
                  </label>
                  <input
                    title="className"
                    className="input-field"
                    value={editForm.class_name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, class_name: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Số điện thoại
                  </label>
                  <input
                    title="phoneNumber"
                    className="input-field"
                    value={editForm.phone}
                    onChange={(e) =>
                      setEditForm({ ...editForm, phone: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 mt-4">
                <p className="font-bold text-blue-900 mb-3 text-sm">
                  Đăng ký môn thi (Mặc định: Toán, Ngữ Văn)
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Môn Tự chọn 1
                    </label>
                    <select
                      title="eSubject1"
                      className="input-field py-2"
                      value={editForm.elective_subject_1}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          elective_subject_1: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">-- Chọn môn 1 --</option>
                      {ELECTIVE_SUBJECTS.map((sub) => (
                        <option key={`1-${sub.code}`} value={sub.code}>
                          {sub.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Môn Tự chọn 2
                    </label>
                    <select
                      title="eSubject2"
                      className="input-field py-2"
                      value={editForm.elective_subject_2}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          elective_subject_2: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">-- Chọn môn 2 --</option>
                      {ELECTIVE_SUBJECTS.map((sub) => (
                        <option key={`2-${sub.code}`} value={sub.code}>
                          {sub.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </form>
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowEditModal(false)}
              >
                Hủy
              </button>
              <button
                type="submit"
                form="edit-form"
                className="btn-primary"
                disabled={saving}
              >
                {saving ? "Đang lưu..." : "Lưu thay đổi"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL IMPORT CSV --- */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b flex justify-between items-center bg-gray-50">
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <FiUpload /> Nhập danh sách thí sinh
              </h3>
              <button
                onClick={() => setShowImportModal(false)}
                className="text-gray-400 hover:text-red-500"
                aria-label="Close import modal"
              >
                <FiXCircle size={24} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[70vh]">
              {!importResult ? (
                <form
                  id="import-form"
                  onSubmit={handleImport}
                  className="space-y-6"
                >
                  <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-lg text-sm">
                    <p className="font-bold mb-2 flex items-center gap-2">
                      <span>
                        VUI LÒNG ĐỌC KỸ HƯỚNG DẪN CẤU TRÚC TỆP CSV DƯỚI ĐÂY:
                      </span>
                      <button
                        type="button"
                        onClick={() => exportAPI.downloadTemplate("student")}
                        className="btn-secondary flex items-center gap-2 text-sm"
                      >
                        <FiDownloadCloud /> Tải mẫu CSV
                      </button>
                    </p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li>
                        Dòng đầu tiên là tiêu đề cột. Dữ liệu bắt đầu từ dòng số
                        2.
                      </li>
                      <li>
                        Tiêu đề các cột bao gồm:{" "}
                        <strong>
                          cccd, full_name, gender, date_of_birth, address,
                          phone, class_name, tuchon1, tuchon2
                        </strong>
                        .
                      </li>
                      <li>
                        Cột ngày sinh (<strong>date_of_birth</strong>) định
                        dạng:{" "}
                        <code className="text-orange-600">YYYY-MM-DD</code>.
                      </li>
                      <li>
                        <strong>Lưu ý:</strong> trước các giá trị số như CCCD,
                        Ngày sinh, Số điện thoại, chèn dấu nháy đơn (
                        <code className="text-orange-600">'</code>) phía trước
                        để không bị mất số 0 hoặc bị chuyển đổi định dạng tự
                        động bởi Excel. Hệ thống sẽ tự động phân tách dấu nháy
                        đơn ra khỏi dữ liệu.
                      </li>
                      <li className="pt-2 opacity-90 border-t border-blue-200 mt-2">
                        <strong>Mã môn Tự chọn (COPY CHÍNH XÁC):</strong>{" "}
                        <code className="font-mono text-red-600">VAT_LI</code>,{" "}
                        <code className="font-mono text-red-600">HOA_HO</code>,{" "}
                        <code className="font-mono text-red-600">SINH_H</code>,{" "}
                        <code className="font-mono text-red-600">DIA_LI</code>,{" "}
                        <code className="font-mono text-red-600">LICH_S</code>,{" "}
                        <code className="font-mono text-red-600">GDKTVL</code>,{" "}
                        <code className="font-mono text-red-600">TIN_HO</code>,{" "}
                        <code className="font-mono text-red-600">CNNG</code>,{" "}
                        <code className="font-mono text-red-600">CNNN</code>,{" "}
                        <code className="font-mono text-red-600">
                          TIENG_ANH
                        </code>
                        ,{" "}
                        <code className="font-mono text-red-600">TIENG_RU</code>
                        ,{" "}
                        <code className="font-mono text-red-600">TIENG_PH</code>
                        ,{" "}
                        <code className="font-mono text-red-600">TIENG_TR</code>
                        ,{" "}
                        <code className="font-mono text-red-600">TIENG_DU</code>
                        ,{" "}
                        <code className="font-mono text-red-600">TIENG_NH</code>
                        ,{" "}
                        <code className="font-mono text-red-600">
                          TIENG_HAN
                        </code>
                        , <code className="font-mono text-red-600">MT</code>.
                      </li>
                      <li>
                        Với mỗi thí sinh, nếu chỉ đăng ký 1 môn tự chọn thì cột{" "}
                        <strong>tuchon1</strong> để môn tự chọn 1, cột còn lại
                        để <code className="font-mono text-red-600">MT</code>.
                        <br></br>Bảng giải thích mã môn tự chọn như sau:
                        <table className="w-full mt-2 text-left text-sm">
                          <thead>
                            <tr className="bg-blue-100">
                              <th className="py-2 px-3 font-bold text-blue-900">
                                Mã môn
                              </th>
                              <th className="py-2 px-3 font-bold text-blue-900">
                                Tên môn
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {ELECTIVE_SUBJECTS.map((sub) => (
                              <tr key={sub.code} className="border-t">
                                <td className="py-2 px-3 font-mono text-red-600">
                                  {sub.code}
                                </td>
                                <td className="py-2 px-3">{sub.name}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </li>
                    </ul>
                  </div>

                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                    <strong className="text-red-600">
                      Sau khi nhập dữ liệu, sẽ KHÔNG thể sửa hoặc xóa Mã định
                      danh, Giới tính và Ngày sinh nữa, hãy kiểm tra kỹ thông
                      tin trước khi nhập.
                    </strong>
                    <input
                      title="importCSVFile"
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                      className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                      required
                    />
                  </div>
                </form>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-gray-50 border p-4 rounded-lg">
                      <p className="text-sm text-gray-500 font-medium">
                        Tổng số dòng
                      </p>
                      <p className="text-2xl font-bold text-gray-900">
                        {importResult.total}
                      </p>
                    </div>
                    <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                      <p className="text-sm text-green-700 font-medium flex items-center justify-center gap-1">
                        <FiCheckCircle /> Thành công
                      </p>
                      <p className="text-2xl font-bold text-green-700">
                        {importResult.imported}
                      </p>
                    </div>
                    <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                      <p className="text-sm text-red-700 font-medium flex items-center justify-center gap-1">
                        <FiAlertCircle /> Lỗi
                      </p>
                      <p className="text-2xl font-bold text-red-700">
                        {importResult.failed}
                      </p>
                    </div>
                  </div>

                  {importResult.errors && importResult.errors.length > 0 && (
                    <div className="border border-red-200 rounded-lg overflow-hidden">
                      <div className="bg-red-50 p-3 border-b border-red-200 font-bold text-red-800 text-sm">
                        Chi tiết các dòng bị lỗi:
                      </div>
                      <ul className="max-h-48 overflow-y-auto p-0 m-0 divide-y divide-gray-100">
                        {importResult.errors.map((err, idx) => (
                          <li key={idx} className="p-3 text-sm flex gap-4">
                            <span className="font-mono bg-red-100 text-red-800 px-2 py-0.5 rounded text-xs whitespace-nowrap h-fit">
                              Dòng {err.row}
                            </span>
                            <span className="text-gray-700">
                              {Array.isArray(err.error)
                                ? err.error.join(", ")
                                : err.error}
                            </span>
                            <span className="text-gray-400 italic">
                              {err.details}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setShowImportModal(false);
                  setImportFile(null);
                  setImportResult(null);
                }}
              >
                {importResult ? "Đóng" : "Hủy"}
              </button>
              {!importResult && (
                <button
                  type="submit"
                  form="import-form"
                  className="btn-primary flex items-center gap-2"
                  disabled={importing || !importFile}
                >
                  {importing ? (
                    "Đang xử lý..."
                  ) : (
                    <>
                      <FiUpload /> Tiến hành Import
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
