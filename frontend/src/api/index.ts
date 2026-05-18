import axiosInstance from "./client";

export const authAPI = {
  register: async (data: {
    username: string;
    email: string;
    password: string;
    full_name: string;
    phone?: string;
    role: string;
  }) => {
    return axiosInstance.post("/auth/register", data);
  },

  login: async (
    cccd: string,
    password: string,
    role: "student" | "teacher" | "admin",
    twoFaCode?: string,
  ) => {
    return axiosInstance.post("/auth/login", {
      cccd,
      password,
      role,
      two_fa_code: twoFaCode,
    });
  },

  refreshToken: async () => {
    return axiosInstance.post("/auth/refresh");
  },

  setupTwoFA: async () => {
    return axiosInstance.post("/auth/setup-2fa");
  },

  verifyTwoFA: async (secret: string, otp: string) => {
    return axiosInstance.post("/auth/verify-2fa", { secret, otp });
  },

  changePassword: async (oldPassword: string, newPassword: string) => {
    return axiosInstance.post("/auth/change-password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  firstLoginChangePassword: async (
    oldPassword: string,
    newPassword: string,
  ) => {
    return axiosInstance.post("/auth/first-login-change-password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
};

export const adminAPI = {
  getDashboard: async () => {
    return axiosInstance.get("/admin/dashboard");
  },

  getTeachers: async () => {
    return axiosInstance.get("/admin/teachers");
  },

  createTeacher: async (teacher: any) => {
    return axiosInstance.post("/admin/teachers", teacher);
  },

  approveTeacher: async (teacherId: number) => {
    return axiosInstance.post(`/admin/teachers/${teacherId}/approve`);
  },

  rejectTeacher: async (teacherId: number, reason: string) => {
    return axiosInstance.post(`/admin/teachers/${teacherId}/reject`, {
      reason,
    });
  },

  getSchools: async () => {
    return axiosInstance.get("/admin/schools");
  },

  addSchool: async (school: any) => {
    return axiosInstance.post("/admin/schools", school);
  },

  getProvinces: async () => {
    return axiosInstance.get("/admin/locations/provinces");
  },

  getWards: async (provinceId?: number) => {
    return axiosInstance.get("/admin/locations/wards", {
      params: provinceId ? { province_id: provinceId } : undefined,
    });
  },

  getStudents: async () => {
    return axiosInstance.get("/admin/students");
  },

  getExamSessions: async () => {
    return axiosInstance.get("/admin/exam-sessions");
  },

  createExamSession: async (session: any) => {
    return axiosInstance.post("/admin/exam-sessions", session);
  },

  publishExamSession: async (sessionId: number) => {
    return axiosInstance.post(`/admin/exam-sessions/${sessionId}/publish`);
  },

  getExamSchedules: async (sessionId?: number) => {
    return axiosInstance.get("/admin/exam-schedules", {
      params: sessionId ? { exam_session_id: sessionId } : undefined,
    });
  },

  createExamSchedule: async (schedule: any) => {
    return axiosInstance.post("/admin/exam-schedules", schedule);
  },

  getSubjects: async () => {
    return axiosInstance.get("/admin/subjects");
  },

  getResults: async (sessionId?: number) => {
    return axiosInstance.get("/admin/results", {
      params: sessionId ? { exam_session_id: sessionId } : undefined,
    });
  },

  publishResults: async (sessionId: number) => {
    return axiosInstance.post(
      `/admin/exam-sessions/${sessionId}/publish-results`,
    );
  },

  // Grading Assignments
  getEssayAssignments: async (sessionId?: number) => {
    return axiosInstance.get("/admin/essay-assignments", {
      params: { exam_session_id: sessionId },
    });
  },
  getEligibleGraders: async () => {
    return axiosInstance.get("/admin/graders");
  },
  assignGrader: async (payload: {
    response_id: number;
    grader_id: number;
    grading_order: number;
  }) => {
    return axiosInstance.post("/admin/essay-assignments/assign", payload);
  },
  removeGraderAssignment: async (gradeId: number) => {
    return axiosInstance.delete(`/admin/essay-assignments/${gradeId}`);
  },
};

export const examAPI = {
  getPapers: async (sessionId?: number) => {
    return axiosInstance.get("/exam/exam-papers", {
      params: sessionId ? { exam_session_id: sessionId } : undefined,
    });
  },

  createPaper: async (paper: any) => {
    return axiosInstance.post("/exam/exam-papers", paper);
  },

  getPaperDetail: async (paperId: number) => {
    return axiosInstance.get(`/exam/exam-papers/${paperId}`);
  },

  updatePaper: async (paperId: number, paper: any) => {
    return axiosInstance.put(`/exam/exam-papers/${paperId}`, paper);
  },

  addQuestion: async (paperId: number, question: any) => {
    return axiosInstance.post(
      `/exam/exam-papers/${paperId}/questions`,
      question,
    );
  },

  updateQuestion: async (questionId: number, question: any) => {
    return axiosInstance.put(`/exam/questions/${questionId}`, question);
  },

  deleteQuestion: async (questionId: number) => {
    return axiosInstance.delete(`/exam/questions/${questionId}`);
  },

  generateVersions: async (paperId: number, numVersions: number) => {
    return axiosInstance.post(
      `/exam/exam-papers/${paperId}/generate-versions`,
      {
        num_versions: numVersions,
      },
    );
  },

  finalizePaper: async (paperId: number) => {
    return axiosInstance.post(`/exam/exam-papers/${paperId}/finalize`);
  },

  addSubsection: async (paperId: number, data: any) => {
    return axiosInstance.post(`/exam/exam-papers/${paperId}/subsections`, data);
  },

  updateSubsection: async (sectionId: number, data: any) => {
    return axiosInstance.put(`/exam/subsections/${sectionId}`, data);
  },

  deleteSubsection: async (sectionId: number) => {
    return axiosInstance.delete(`/exam/subsections/${sectionId}`);
  },
  importQuestionsCsv: async (
    paperId: number,
    part: string,
    questionType: string,
    file: File,
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("part", part);
    formData.append("question_type", questionType);
    return axiosInstance.post(
      `/exam/exam-papers/${paperId}/import-questions`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
  },

  reorderQuestions: async (paperId: number, orderedQuestionIds: number[]) => {
    return axiosInstance.post(`/exam/exam-papers/${paperId}/reorder`, {
      ordered_question_ids: orderedQuestionIds,
    });
  },
};

export const teacherAPI = {
  // Student Management (GVQL)
  getStudents: async () => {
    return axiosInstance.get("/teacher/students");
  },

  addStudent: async (student: any) => {
    return axiosInstance.post("/teacher/students", student);
  },

  updateStudent: async (studentId: number, student: any) => {
    return axiosInstance.put(`/teacher/students/${studentId}`, student);
  },

  deleteStudent: async (studentId: number) => {
    return axiosInstance.delete(`/teacher/students/${studentId}`);
  },

  resetStudentPassword: async (studentId: number) => {
    return axiosInstance.post(`/teacher/students/${studentId}/reset-password`);
  },

  // Exam Management (for exams created by teacher)
  getExams: async () => {
    return axiosInstance.get("/teacher/exams");
  },

  createExam: async (exam: any) => {
    return axiosInstance.post("/teacher/exams", exam);
  },

  getExamDetail: async (examId: number) => {
    return axiosInstance.get(`/teacher/exams/${examId}`);
  },

  updateExam: async (examId: number, exam: any) => {
    return axiosInstance.put(`/teacher/exams/${examId}`, exam);
  },

  addQuestion: async (examId: number, question: any) => {
    return axiosInstance.post(`/teacher/exams/${examId}/questions`, question);
  },

  // Dashboard
  getDashboard: async () => {
    return axiosInstance.get("/teacher/dashboard");
  },

  // Grading
  getStudentsToGrade: async () => {
    return axiosInstance.get("/teacher/grade-students");
  },

  gradeEssay: async (responseId: number, score: number, feedback: string) => {
    return axiosInstance.post(`/teacher/grade/${responseId}`, {
      score,
      feedback,
    });
  },

  // Import students from CSV file
  importStudents: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return axiosInstance.post("/teacher/students/import", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  getSchoolResults: async (schoolId: number) => {
    return axiosInstance.get(`/teacher/school-results/${schoolId}`);
  },

  getMySchoolId: async (userId: number) => {
    const response = await axiosInstance.get(`/teacher/school-id/${userId}`);
    return response.data.school_id;
  },
};

export const studentAPI = {
  getDashboard: async () => {
    return axiosInstance.get("/student/dashboard");
  },
  getExams: async () => {
    return axiosInstance.get("/student/exam-schedule");
  },
  startExam: async (scheduleId: number) => {
    return axiosInstance.post(`/student/exam-attempts/${scheduleId}/start`);
  },
  getExamPaper: async (attemptId: number) => {
    return axiosInstance.get(`/student/exam-attempts/${attemptId}/paper`);
  },
  submitAnswer: async (
    attemptId: number,
    questionId: number,
    answer: any,
    track?: string,
  ) => {
    const payload: any = {
      question_id: questionId,
      student_answer: answer,
    };
    if (track) payload.selected_informatics_track = track;
    return axiosInstance.post(
      `/exam/exam-attempts/${attemptId}/responses`,
      payload,
    );
  },
  submitExam: async (attemptId: number) => {
    return axiosInstance.post(`/exam/exam-attempts/${attemptId}/submit`);
  },
  getAttemptStatus: async (attemptId: number) => {
    return axiosInstance.get(`/exam/exam-attempts/${attemptId}/status`);
  },
  getResults: async () => {
    return axiosInstance.get("/student/results");
  },
  getResult: async (resultId: number) => {
    return axiosInstance.get(`/student/results/${resultId}`);
  },
};

export const uploadAPI = {
  uploadImage: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return axiosInstance.post("/upload/image", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  deleteImage: async (filename: string) => {
    return axiosInstance.delete(`/upload/image/${filename}`);
  },
};

export const gradingAPI = {
  getEssays: async (params?: any) => {
    return axiosInstance.get("/grading/essays", { params });
  },
  getEssayDetail: async (essayGradeId: number) => {
    return axiosInstance.get(`/grading/essays/${essayGradeId}`);
  },
  submitGrade: async (
    essayGradeId: number,
    score: number,
    feedback: string,
  ) => {
    return axiosInstance.post(`/grading/essays/${essayGradeId}/grade`, {
      score,
      feedback,
    });
  },
};

const handleBlobDownload = (response: any, defaultFilename: string) => {
  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;

  const disposition = response.headers['content-disposition'];
  let filename = defaultFilename;
  if (disposition && disposition.indexOf('attachment') !== -1) {
    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
    const matches = filenameRegex.exec(disposition);
    if (matches != null && matches[1]) {
      filename = matches[1].replace(/['"]/g, '');
    }
  }

  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const exportAPI = {
  exportStudents: async (exportType: 'csv' | 'xlsx', filters?: any) => {
    const response = await axiosInstance.post(`/export/data/students/${exportType}`, filters || {}, {
      responseType: 'blob'
    });
    handleBlobDownload(response, `Danh_Sach_Hoc_Sinh.${exportType}`);
    return response;
  },

  exportResults: async (exportType: 'csv' | 'xlsx', filters: { exam_session_id: number; subject_id?: number }) => {
    const response = await axiosInstance.post(`/export/data/results/${exportType}`, filters, {
      responseType: 'blob'
    });
    handleBlobDownload(response, `Ket_Qua_Thi.${exportType}`);
    return response;
  },

  exportSchoolResults: async (exportType: 'csv' | 'xlsx', filters: { exam_session_id: number }) => {
    const response = await axiosInstance.post(`/export/data/school_results/${exportType}`, filters, {
      responseType: 'blob'
    });
    handleBlobDownload(response, `Ket_Qua_Toan_Truong.${exportType}`);
    return response;
  },

  downloadTemplate: async (templateType: 'student' | 'question_mc' | 'question_tf' | 'question_sa') => {
    const response = await axiosInstance.get(`/export/template/${templateType}`, {
      responseType: 'blob'
    });
    const typeName = templateType === 'student' ? '_Hoc_Sinh' :
                     templateType === 'question_mc' ? '_Cau_Hoi_Trac_Nghiem' :
                     templateType === 'question_tf' ? '_Cau_Hoi_Dung_Sai' :
                     templateType === 'question_sa' ? '_Cau_Hoi_Tra_Loi_Ngan' : '';
    handleBlobDownload(response, `Mau_Nhap_Lieu${typeName}.csv`);
    return response;
  }
}