$(document).ready(function() {
    $('.usedatepicker').datepicker({
        dateFormat: 'dd/mm/yy',
        changeMonth: true,
        changeYear: true,
        allowInputToggle: true
    });
    let pendidikan_formal_ids_length = 0
    $('.table_pendidikan_formal_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;">
                <select class="form-control s_website_form_input" name="pendidikan_formal_ids__pendidikan__`+pendidikan_formal_ids_length+`" required="True" style="font-size: 14px;">
                    <option value="SD">SD</option>
                    <option value="SMP">SMP</option>
                    <option value="SMA">SMA</option>
                    <option value="S1">S1</option>
                    <option value="S2">S2</option>
                    <option value="S3">S3</option>
                </select>
            </td>
            <td style="padding: unset;"><input name="pendidikan_formal_ids__nama_sekolah__`+pendidikan_formal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_formal_ids__jurusan__`+pendidikan_formal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_formal_ids__tahun_mulai__`+pendidikan_formal_ids_length+`" required="" class="form-control" type="number" style="padding: unset;padding-left: 5px;font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_formal_ids__tahun_akhir__`+pendidikan_formal_ids_length+`" required="" class="form-control" type="number" style="padding: unset;padding-left: 5px;font-size: 14px;"/></td>
            <td style="padding: unset;">
                <select class="form-control s_website_form_input" name="pendidikan_formal_ids__ijazah__`+pendidikan_formal_ids_length+`" required="True" style="font-size: 14px;">
                    <option value="ada">Ada</option>
                    <option value="tidak_ada">Tidak Ada</option>
                </select>
            </td>
            <td style="padding: unset;"><input name="pendidikan_formal_ids__ipk__`+pendidikan_formal_ids_length+`" step="0.01" required="" class="form-control" type="number" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_formal_ids__kota__`+pendidikan_formal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        pendidikan_formal_ids_length = pendidikan_formal_ids_length+1
        $(line).insertBefore('.table_pendidikan_formal_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_pendidikan_formal_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

    let pendidikan_nonformal_ids_length = 0
    $('.table_pendidikan_nonformal_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="pendidikan_nonformal_ids__courses__`+pendidikan_nonformal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_nonformal_ids__lembaga_pendidikan__`+pendidikan_nonformal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_nonformal_ids__tahun_mulai__`+pendidikan_nonformal_ids_length+`" required="" class="form-control" type="number" style="padding: unset;padding-left: 5px;font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_nonformal_ids__tahun_akhir__`+pendidikan_nonformal_ids_length+`" required="" class="form-control" type="number" style="padding: unset;padding-left: 5px;font-size: 14px;"/></td>
            <td style="padding: unset;">
                <select class="form-control s_website_form_input" name="pendidikan_nonformal_ids__ijazah__`+pendidikan_nonformal_ids_length+`" required="True" style="font-size: 14px;">
                    <option value="ada">Ada</option>
                    <option value="tidak_ada">Tidak Ada</option>
                </select>
            </td>
            <td style="padding: unset;"><input name="pendidikan_nonformal_ids__tingkat__`+pendidikan_nonformal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="pendidikan_nonformal_ids__kota__`+pendidikan_nonformal_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        pendidikan_nonformal_ids_length = pendidikan_nonformal_ids_length+1
        $(line).insertBefore('.table_pendidikan_nonformal_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_pendidikan_nonformal_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

    let organization_ids_length = 0
    $('.table_organization_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="organization_ids__name__`+organization_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="organization_ids__jenis_kegiatan__`+organization_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="organization_ids__position__`+organization_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="organization_ids__tahun__`+organization_ids_length+`" required="" class="form-control" type="number" style="padding: unset;padding-left: 5px;font-size: 14px;"/></td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        organization_ids_length = organization_ids_length+1
        $(line).insertBefore('.table_organization_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_organization_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });


    $('#table_family .fa-trash').click(function() {
        $($(this).parents()[1]).remove()
    });

    let anak_ids_length = 0
    $('.table_anak_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="anak_ids__name__`+anak_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="anak_ids__tempat_lahir__`+anak_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="anak_ids__tanggal_lahir__`+anak_ids_length+`" required="" readonly="" class="form-control usedatepicker" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;">
            <select class="form-control s_website_form_input" name="anak_ids__jenis_kelamin__`+anak_ids_length+`" required="True" style="font-size: 14px;text-align: center;font-weight: bold;">
                <option value="L">Laki-laki</option>
                <option value="P">Perempuan</option>
            </select>
            </td>
            <td style="padding: unset;"><input name="anak_ids__no_handphone__`+anak_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="anak_ids__pendidikan__`+anak_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="anak_ids__pekerjaan__`+anak_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        anak_ids_length = anak_ids_length+1
        $(line).insertBefore('.table_anak_ids_add_line');
        $('.usedatepicker').datepicker({
            dateFormat: 'dd/mm/yy',
            changeMonth: true,
            changeYear: true,
            allowInputToggle: true
        });
        $('#table_anak_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

    
    let saudara_ids_length = 0
    $('.table_saudara_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="saudara_ids__name__`+saudara_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="saudara_ids__tempat_lahir__`+saudara_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="saudara_ids__tanggal_lahir__`+saudara_ids_length+`" required="" readonly="" class="form-control usedatepicker" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;">
            <select class="form-control s_website_form_input" name="saudara_ids__jenis_kelamin__`+saudara_ids_length+`" required="True" style="font-size: 14px;text-align: center;font-weight: bold;">
                <option value="L">Laki-laki</option>
                <option value="P">Perempuan</option>
            </select>
            </td>
            <td style="padding: unset;"><input name="saudara_ids__no_handphone__`+saudara_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="saudara_ids__pendidikan__`+saudara_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="saudara_ids__pekerjaan__`+saudara_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        saudara_ids_length = saudara_ids_length+1
        $(line).insertBefore('.table_saudara_ids_add_line');
        $('.usedatepicker').datepicker({
            dateFormat: 'dd/mm/yy',
            changeMonth: true,
            changeYear: true,
            allowInputToggle: true
        });
        $('#table_saudara_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

    let work_experience_ids_length = 0
    $('.tbl_work_experience_ids_add_line').click(function() {
        var line = `<div class="col-sm-12 py-2" style="border-bottom: 1px solid #DEE2E6;">
            <div class="row">
                <div class="col-sm-6">
                    <div class="mb-2">
                        <label for="work_experience_ids__name__`+work_experience_ids_length+`" class="form-label">Nama Perusahaan</label>
                        <input type="text" required="true" class="form-control" id="work_experience_ids__name__`+work_experience_ids_length+`" name="work_experience_ids__name__`+work_experience_ids_length+`" />
                    </div>
                    <div class="mb-2">
                        <label for="work_experience_ids__alamat__`+work_experience_ids_length+`" class="form-label">Alamat lengkap &amp; No Telepon</label>
                        <input type="text" required="true" class="form-control" id="work_experience_ids__alamat__`+work_experience_ids_length+`" name="work_experience_ids__alamat__`+work_experience_ids_length+`" />
                    </div>
                    <div class="mb-2">
                        <label for="work_experience_ids__jobdesk__`+work_experience_ids_length+`" class="form-label">Tugas &amp; Tanggung Jawab</label>
                        <textarea required="true" class="form-control" id="work_experience_ids__jobdesk__`+work_experience_ids_length+`" name="work_experience_ids__jobdesk__`+work_experience_ids_length+`" rows="6"></textarea>
                    </div>
                </div>
                <div class="col-sm-6">
                    <div class="row">
                        <div class="col-sm-6 mb-2">
                            <label for="work_experience_ids__mulai__`+work_experience_ids_length+`" class="form-label">Mulai</label>
                            <input type="date" required="true" class="form-control" id="work_experience_ids__mulai__`+work_experience_ids_length+`" name="work_experience_ids__mulai__`+work_experience_ids_length+`" />
                        </div>
                        <div class="col-sm-6 mb-2">
                            <label for="work_experience_ids__selesai__`+work_experience_ids_length+`" class="form-label">Sampai</label>
                            <input type="date" required="true" class="form-control" id="work_experience_ids__selesai__`+work_experience_ids_length+`" name="work_experience_ids__selesai__`+work_experience_ids_length+`"/>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label for="work_experience_ids__jabatan__`+work_experience_ids_length+`" class="form-label">Jabatan</label>
                        <input type="text" required="true" class="form-control" id="work_experience_ids__jabatan__`+work_experience_ids_length+`" name="work_experience_ids__jabatan__`+work_experience_ids_length+`" />
                    </div>
                    <div class="mb-2">
                        <label for="work_experience_ids__salary__`+work_experience_ids_length+`" class="form-label">Gaji</label>
                        <input type="number" step="0.01" required="true" class="form-control" id="work_experience_ids__salary__`+work_experience_ids_length+`" name="work_experience_ids__salary__`+work_experience_ids_length+`" />
                    </div>
                    <div class="mb-2">
                        <label for="work_experience_ids__alasan_keluar__`+work_experience_ids_length+`" class="form-label">Alasan Keluar</label>
                        <textarea required="true" class="form-control" id="work_experience_ids__alasan_keluar__`+work_experience_ids_length+`" name="work_experience_ids__alasan_keluar__`+work_experience_ids_length+`" rows="3"></textarea>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-sm-6 work_experience_ids_delete" style="color: red; cursor:pointer;"><i class="fa fa-trash"></i> Delete</div>
            </div>
        </div>`;
        work_experience_ids_length = work_experience_ids_length+1
        $(line).insertBefore('.tbl_work_experience_ids_add_line');
        $('.usedatepicker').datepicker({
            dateFormat: 'dd/mm/yy',
            changeMonth: true,
            changeYear: true,
            allowInputToggle: true
        });
        $('#tbl_work_experience_ids .work_experience_ids_delete').click(function() {
            $($(this).parents()[1]).remove()
        });
    });


    let foreign_language_ids_length = 0
    $('.table_foreign_language_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="foreign_language_ids__name__`+foreign_language_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;">
            <select class="form-control s_website_form_input" name="foreign_language_ids__tingkat__`+foreign_language_ids_length+`" required="True" style="font-size: 14px;text-align: center;font-weight: bold;">
                <option value="aktif">Aktif</option>
                <option value="pasif">Pasif</option>
            </select>
            </td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        foreign_language_ids_length = foreign_language_ids_length+1
        $(line).insertBefore('.table_foreign_language_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_foreign_language_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

    let local_language_ids_length = 0
    $('.table_local_language_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="local_language_ids__name__`+local_language_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;">
            <select class="form-control s_website_form_input" name="local_language_ids__tingkat__`+local_language_ids_length+`" required="True" style="font-size: 14px;text-align: center;font-weight: bold;">
                <option value="aktif">Aktif</option>
                <option value="pasif">Pasif</option>
            </select>
            </td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        local_language_ids_length = local_language_ids_length+1
        $(line).insertBefore('.table_local_language_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_local_language_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });


    let skill_ids_length = 0
    $('.table_skill_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="skill_ids__name__`+skill_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;">
            <select class="form-control s_website_form_input" name="skill_ids__tingkat__`+skill_ids_length+`" required="True" style="font-size: 14px;text-align: center;font-weight: bold;">
                <option value="baik_sekali">Baik Sekali</option>
                <option value="baik">Baik</option>
                <option value="cukup">Cukup</option>
                <option value="kurang">Kurang</option>
            </select>
            </td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        skill_ids_length = skill_ids_length+1
        $(line).insertBefore('.table_skill_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_skill_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

    
    let table_reference_ids_length = 0
    $('.table_reference_ids_add_line').click(function() {
        var line = `<tr class="input_data">
            <td style="padding: unset;"><input name="reference_ids__name__`+table_reference_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="reference_ids__nama_perusahaan__`+table_reference_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="reference_ids__jabatan__`+table_reference_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;"><input name="reference_ids__alamat__`+table_reference_ids_length+`" required="" class="form-control" type="text" style="font-size: 14px;"/></td>
            <td style="padding: unset;" class="text-center"><i class="fa fa-trash" style="cursor:pointer;"></i></td>
        </tr>`;
        table_reference_ids_length = table_reference_ids_length+1
        $(line).insertBefore('.table_reference_ids_add_line');
        // $('.usedatepicker').datepicker({
        //     dateFormat: 'dd/mm/yy',
        //     changeMonth: true,
        //     changeYear: true,
        //     allowInputToggle: true
        // });
        $('#table_reference_ids .fa-trash').click(function() {
            $($(this).parents()[1]).remove()
        });
    });

});