import React, { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { adminAPI } from "@/api";
import { FiPlus } from "react-icons/fi";

interface School {
  school_id: number;
  school_name: string;
  display_name: string;
  address: string;
  phone: string;
  email: string;
  district_name?: string;
  province_name?: string;
}

interface Province {
  province_id: number;
  province_name: string;
  province_code?: string;
}

interface Ward {
  district_id: number;
  district_name: string;
  province_id: number;
}

export default function SchoolsPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [provinces, setProvinces] = useState<Province[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    province_id: "",
    district_id: "",
    school_name: "",
    address: "",
    phone: "",
    email: "",
  });

  const selectedProvinceId = useMemo(
    () => (form.province_id ? Number(form.province_id) : undefined),
    [form.province_id],
  );

  const fetchInitialData = async () => {
    try {
      const [schoolsResponse, provincesResponse] = await Promise.all([
        adminAPI.getSchools(),
        adminAPI.getProvinces(),
      ]);
      setSchools(schoolsResponse.data.data || []);
      setProvinces(provincesResponse.data.data || []);
    } catch (error: any) {
      toast.error(
        error.response?.data?.error || "Không thể tải dữ liệu trường",
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchWards = async (provinceId?: number) => {
    if (!provinceId) {
      setWards([]);
      return;
    }
    try {
      const response = await adminAPI.getWards(provinceId);
      setWards(response.data.data || []);
    } catch (error: any) {
      toast.error(
        error.response?.data?.error || "Không thể tải danh sách xã/phường",
      );
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchWards(selectedProvinceId);
  }, [selectedProvinceId]);

  const createSchool = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await adminAPI.addSchool({
        ...form,
        province_id: Number(form.province_id),
        district_id: Number(form.district_id),
      });
      toast.success("Đã tạo trường");
      setForm({
        province_id: "",
        district_id: "",
        school_name: "",
        address: "",
        phone: "",
        email: "",
      });
      fetchInitialData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || "Không thể tạo trường");
    }
  };

  if (loading) return <div className="text-center py-8">Đang tải...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Quản Lý Trường</h1>
        <p className="text-gray-500 mt-1">
          Tạo trường theo tỉnh/thành và xã/phường để tránh trùng lặp khi chọn
          trường.
        </p>
      </div>

      <form onSubmit={createSchool} className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <FiPlus /> Tạo trường
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <select
            className="input-field"
            value={form.province_id}
            onChange={(e) =>
              setForm({ ...form, province_id: e.target.value, district_id: "" })
            }
            required
          >
            <option value="">Chọn tỉnh/thành</option>
            {provinces.map((province) => (
              <option key={province.province_id} value={province.province_id}>
                {province.province_code
                  ? `${province.province_code} - ${province.province_name}`
                  : `${province.province_id} - ${province.province_name}`}
              </option>
            ))}
          </select>
          <select
            className="input-field"
            value={form.district_id}
            onChange={(e) => setForm({ ...form, district_id: e.target.value })}
            disabled={!form.province_id}
            required
          >
            <option value="">Chọn xã/phường</option>
            {wards.map((ward) => (
              <option key={ward.district_id} value={ward.district_id}>
                {ward.district_name}
              </option>
            ))}
          </select>
          <input
            className="input-field md:col-span-2"
            placeholder="Tên trường"
            value={form.school_name}
            onChange={(e) => setForm({ ...form, school_name: e.target.value })}
            required
          />
          <input
            className="input-field md:col-span-2"
            placeholder="Địa chỉ chi tiết"
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
          />
          <input
            className="input-field"
            placeholder="SĐT"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
          <input
            className="input-field"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <button className="btn-primary md:col-start-4">Tạo trường</button>
        </div>
      </form>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-3 px-4">Trường</th>
                <th className="text-left py-3 px-4">Tỉnh/thành</th>
                <th className="text-left py-3 px-4">Xã/phường</th>
                <th className="text-left py-3 px-4">Địa chỉ</th>
                <th className="text-left py-3 px-4">Liên hệ</th>
              </tr>
            </thead>
            <tbody>
              {schools.map((school) => (
                <tr
                  key={school.school_id}
                  className="border-b hover:bg-gray-50"
                >
                  <td className="py-3 px-4 font-medium">
                    {school.display_name || school.school_name}
                  </td>
                  <td className="py-3 px-4">{school.province_name}</td>
                  <td className="py-3 px-4">{school.district_name}</td>
                  <td className="py-3 px-4">{school.address}</td>
                  <td className="py-3 px-4">{school.phone || school.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
