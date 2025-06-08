def thong_ke_su_kien_theo_tu_khoa(self, tu_khoa, nguong=0.6):
    danh_sach = FileManager.doc_file(self.path)
    su_kien_lien_quan = []

    for dong in danh_sach:
        if "||" in dong:
            _, nd = dong.split("||", 1)
            if tu_khoa.lower() in nd.lower():
                su_kien_lien_quan.append(nd.strip())

    if not su_kien_lien_quan:
        print(f"❌ Không có sự kiện nào chứa từ khóa: '{tu_khoa}'")
        return

    nhom_giong_nhau = []
    da_xet = set()

    for i, sk in enumerate(su_kien_lien_quan):
        if i in da_xet:
            continue
        nhom = [sk]
        da_xet.add(i)
        for j in range(i + 1, len(su_kien_lien_quan)):
            if j in da_xet:
                continue
            do_giong = difflib.SequenceMatcher(None, sk, su_kien_lien_quan[j]).ratio()
            if do_giong >= nguong:
                nhom.append(su_kien_lien_quan[j])
                da_xet.add(j)
        if len(nhom) > 1:
            nhom_giong_nhau.append(nhom)

    if nhom_giong_nhau:
        print(f"📊 Các nhóm sự kiện gần giống nhau chứa từ khóa '{tu_khoa}':")
        for idx, nhom in enumerate(nhom_giong_nhau, 1):
            print(f"\n🧩 Nhóm {idx}:")
            for sk in nhom:
                print(" -", sk)
    else:
        print(f"✅ Không có sự kiện nào trùng lặp gần giống nhau với từ khóa '{tu_khoa}'.")
