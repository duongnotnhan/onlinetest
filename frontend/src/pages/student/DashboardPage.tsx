import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { studentAPI } from "@/api";
import toast from "react-hot-toast";
import { FiClock } from "react-icons/fi";

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [exams, setExams] = useState<any[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const fetchExams = async () => {
      try {
        const response = await studentAPI.getDashboard();
        setProfile(response.data.profile);
        setExams(response.data.schedules || []);
      } catch (error) {
        toast.error("Lỗi tải danh sách kỳ thi: " + (error as Error).message);
      } finally {
        setLoading(false);
      }
    };
    fetchExams();
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleStartExam = async (scheduleId: number) => {
    try {
      const res = await studentAPI.startExam(scheduleId);
      navigate(`/student/take-exam/${res.data.attempt_id}`);
    } catch (error: any) {
      toast.error(
        error.response?.data?.error ||
          "Chưa đến giờ mở đề hoặc tài khoản không hợp lệ: " + (error as Error).message,
      );
    }
  };

  const renderExamStatus = (exam: any) => {
    if (exam.status === "completed" || exam.status === "graded") {
      return (
        <span className="text-emerald-700 font-medium text-xs px-2.5 py-1 bg-emerald-50 rounded-md border border-emerald-100">
          Đã nộp bài
        </span>
      );
    }

    const startStr = `${exam.exam_date}T${exam.start_time}`;
    const endStr = `${exam.exam_date}T${exam.end_time}`;
    const startTime = new Date(startStr);
    const endTime = new Date(endStr);

    if (now < startTime) {
      const diff = Math.floor((startTime.getTime() - now.getTime()) / 1000);
      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      const s = diff % 60;
      return (
        <span className="text-amber-700 font-medium text-xs flex items-center gap-1 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-100">
          <FiClock size={12} /> Mở sau {h}h {m}p {s}s
        </span>
      );
    } else if (now >= startTime && now <= endTime) {
      if (exam.attempt_id) {
        return (
          <button
            onClick={() => navigate(`/student/take-exam/${exam.attempt_id}`)}
            className="btn-secondary py-1 px-3 text-xs border-blue-300 text-blue-700"
          >
            Tiếp tục làm bài
          </button>
        );
      }
      return (
        <button
          onClick={() => handleStartExam(exam.schedule_id)}
          className="btn-primary py-1 px-3 text-xs"
        >
          Vào phòng thi
        </button>
      );
    } else {
      return (
        <span className="text-rose-700 font-medium text-xs bg-rose-50 px-2.5 py-1 rounded-md border border-rose-100">
          Đã kết thúc
        </span>
      );
    }
  };

  if (loading)
    return (
      <div className="text-center py-8 text-sm font-medium text-gray-500">
        Đang tải phòng thi...
      </div>
    );

  return (
    <div className="space-y-6">
      {profile && (
        <div className="card">
          <div className="flex flex-col sm:flex-row gap-4 sm:items-center">
            <div className="h-16 w-16 rounded-full bg-gray-100 border border-gray-200 overflow-hidden flex items-center justify-center font-bold text-gray-500 text-xl shrink-0">
              {profile.has_profile_photo ? (
                <img
                  src="/api/student/profile/photo"
                  alt="avatar"
                  className="h-full w-full object-cover"
                />
              ) : (
                profile.full_name[0]
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-1.5 text-sm text-gray-700 flex-1">
              <p>
                <span className="text-gray-400 font-medium">Họ tên:</span>{" "}
                <strong className="text-gray-900">{profile.full_name}</strong>
              </p>
              <p>
                <span className="text-gray-400 font-medium">Ngày sinh:</span>{" "}
                <strong className="text-gray-900">
                  {profile.date_of_birth}
                </strong>
              </p>
              <p>
                <span className="text-gray-400 font-medium">CCCD:</span>{" "}
                <span className="font-mono bg-gray-50 border border-gray-200 px-1.5 py-0.5 rounded text-xs">
                  {profile.cccd}
                </span>
              </p>
              <p>
                <span className="text-gray-400 font-medium">Đơn vị:</span>{" "}
                <strong className="text-gray-900">
                  {profile.class_name} - {profile.school_name}
                </strong>
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        <div className="bg-gray-50 p-4 border-b border-gray-100">
          <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wide">
            Lịch Thi Đăng Ký
          </h2>
        </div>
        <div className="p-4 space-y-3">
          {exams.map((exam) => (
            <div
              key={exam.schedule_id}
              className="border border-gray-100 rounded-lg p-3.5 hover:bg-gray-50/50 transition-colors flex flex-col sm:flex-row justify-between sm:items-center gap-3"
            >
              <div>
                <h3 className="font-bold text-sm text-gray-900">
                  {exam.subject_name}
                </h3>
                <p className="text-xs text-gray-500 mt-1 flex items-center gap-1.5">
                  <FiClock size={12} className="text-gray-400" />{" "}
                  {exam.exam_date} | {exam.start_time.substring(0, 5)} -{" "}
                  {exam.end_time.substring(0, 5)} ({exam.duration_minutes} phút)
                </p>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 border-t sm:border-t-0 pt-2 sm:pt-0 border-gray-100">
                {renderExamStatus(exam)}
                {exam.score !== null && (
                  <span className="text-sm font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                    Điểm: {exam.score}
                  </span>
                )}
              </div>
            </div>
          ))}
          {exams.length === 0 && (
            <p className="text-gray-400 py-6 italic text-center text-xs">
              Chưa có lịch thi phân bổ.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
