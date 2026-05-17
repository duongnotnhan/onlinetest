import { ReactNode } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900 antialiased overflow-hidden">
      {/* Khung thanh bên (Sidebar) cố định trọn chiều cao bên trái */}
      <Sidebar />

      {/* Vùng bên phải chứa thanh điều hướng (Navbar) và phần nội dung chính */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <Navbar />

        {/* Khung nội dung trung tâm: Bọc đệm lề (padding) chuẩn và giới hạn max-w-7xl để các hộp (box) hiển thị rõ ràng, không bị dính lề */}
        <main className="flex-1 overflow-y-auto w-full p-4 sm:p-6 md:p-8 transition-all duration-300">
          <div className="max-w-7xl mx-auto w-full">{children}</div>
        </main>
      </div>
    </div>
  );
}
