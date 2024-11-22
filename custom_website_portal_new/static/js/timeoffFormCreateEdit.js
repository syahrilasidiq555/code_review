document.addEventListener('alpine:init', async () => {
    Alpine.store('timeoffStore', {
        active_id : 0,
        timeoff: {
            name: '',
            employee_id: '',
            holiday_status_id: '',
            date_from: '',
            date_to: '',
            request_date_from: '',
            request_date_to: '',
            request_date_from_period:'',
            state: 'draft',
            
        },
        old_timeoff : {},
        alert: {
            show: false,
            message: 'ini alert message',
            iconHref: "#check-circle-fill",
            class: 'alert-success',
        },
        editForm: false,
        isShortTimeWork: false,
        isAllowDoc: false,
        showButtonEdit:true,

        attachments: [],
        newAttachments:[],

        demaskMoney(value) {
            return value.replaceAll(',', '')
        },
        action_edit(){
            this.old_timeoff = {...this.timeoff}
            this.editForm =  true
        },
        action_cancel(){
            if (!this.active_id) {
                // cancel dalam create mode
                let isConfirmed = confirm('The record has been modified, your changes will be discarded. Do you want to proceed')
                if (isConfirmed) {
                    window.setTimeout(function(){window.location.href = `/portals/time-off`},500)
                }
            } else {
                // cancel dalam edit mode
                this.alert.show = false
                if (JSON.stringify(this.timeoff) === JSON.stringify(this.old_timeoff) & this.newAttachments.length == 0) {
                    this.editForm = false
                } else {
                    let isConfirmed = confirm('The record has been modified, your changes will be discarded. Do you want to proceed')
                    if (isConfirmed) {
                        this.timeoff = {...this.old_timeoff}
                        this.editForm = false
                        this.newAttachments = []
                        document.getElementById('documents').value = null;
                    }
                    
                }
            }
        },

        changeAttachment(e){
            // console.log(e.target.files) 
            this.newAttachments = []
            for (let file of e.target.files) {
                // validasi max size 10MB
                if (file.size > 10000000) {
                    alert("Can't add attachment that has size more than 10 MB!");
                    document.getElementById('documents').value = null;
                    this.newAttachments = []
                    document.getElementById("addDocumentFiles").innerHTML = "Add Files"
                } else {
                    var reader = new FileReader();
                    reader.readAsDataURL(file);

                    reader.onload = z => {
                        this.newAttachments.push({
                            name: file.name,
                            size: this.formatBytes(file.size),
                            file: z.target.result
                        })
                    }

                    if (e.target.files) {
                        document.getElementById("addDocumentFiles").innerHTML = "Change Files"
                    } else {
                        document.getElementById("addDocumentFiles").innerHTML = "Add Files"
                    }
                }
                
            }
            
            
        },

        formatBytes(bytes, decimals = 2) {
            if (!+bytes) return '0 Bytes'
        
            const k = 1024
            const dm = decimals < 0 ? 0 : decimals
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
        
            const i = Math.floor(Math.log(bytes) / Math.log(k))
        
            return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
        },

        validateData(){
            this.alert.show = false
            
            if (this.timeoff.holiday_status_id == '0') {
                this.alert.show = true
                this.alert.message = 'Time Off Type must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            // if (this.attendance.attendance_type == '0') {
            //     this.alert.show = true
            //     this.alert.message = 'Attendance Type must be choosed!'
            //     this.alert.class = 'alert-danger'
            //     return true
            // }
            // if (!this.attendance.task) {
            //     this.alert.show = true
            //     this.alert.message = 'Task must be filled!'
            //     this.alert.class = 'alert-danger'
            //     return true
            // }
            if (!this.timeoff.name) {
                this.alert.show = true
                this.alert.message = 'Description must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!this.timeoff.request_date_from) {
                this.alert.show = true
                this.alert.message = 'Start Date must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            
            console.log("this.isShortTimeWork")
            console.log(this.isShortTimeWork)
            console.log("this.timeoff.holiday_status_id")
            console.log(this.timeoff.holiday_status_id)

            if (!this.isShortTimeWork && !this.timeoff.request_date_to) {
                this.alert.show = true
                this.alert.message = 'End Date must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            // if (this.attendance.attendance_type != 'wfh' && !parseInt(this.attendance.partner_id)) {
            //     this.alert.show = true
            //     this.alert.message = 'Project Customer must be choosed!'
            //     this.alert.class = 'alert-danger'
            //     return true
            // }
            if (!parseInt(this.timeoff.approver_id)) {
                this.alert.show = true
                this.alert.message = 'Approver must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!parseInt(this.timeoff.pm_leader_id)) {
                this.alert.show = true
                this.alert.message = 'PM / Leader must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            // if (!parseInt(this.attendance.location_id)) {
            //     this.alert.show = true
            //     this.alert.message = 'Location must be choosed!'
            //     this.alert.class = 'alert-danger'
            //     return true
            // }
        },

        async compute_holiday_short() {
            const settings = {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "jsonrpc": "2.0",
                    "params": {
                        "values": {},
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_leave/get_type_holiday/${this.timeoff.holiday_status_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                    return
                }
                else {
                    this.isShortTimeWork = data.result.type == 'half_day'
                    this.isAllowDoc = data.result.support_document == true
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                }
            } catch (e) {
                return e;
            }
        },
        
        async createData(){
            isErrorValidate = this.validateData()
            if (isErrorValidate) {
                return
            }

            // make sure not click this twice
            this.editForm = !this.editForm
            this.alert.message = 'Loading.....'
            this.alert.class =  'alert-secondary'
            this.alert.show = true

            const settings = {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "jsonrpc": "2.0",
                    "params": {
                        "values": {
                            name: this.timeoff.name,
                            employee_id: parseInt(this.timeoff.employee_id),
                            holiday_status_id: parseInt(this.timeoff.holiday_status_id),
                            request_date_from: this.timeoff.request_date_from.toLocaleString(),
                            request_date_to: this.timeoff.request_date_to.toLocaleString(),
                            approver_id : parseInt(this.timeoff.approver_id),
                            pm_leader_id : parseInt(this.timeoff.pm_leader_id),
                            request_date_from_period : this.timeoff.request_date_from_period,
                        },
                        "documents": this.newAttachments,
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_leave/create`, settings);
                const data = await fetchResponse.json();
                // console.log(data)
                if (data.result.status != 'success') {
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                    return
                }
                else {
                    // this.editForm = !this.editForm
                    this.alert.message = data['result']['message']
                    this.alert.class =  'alert-success'
                    this.alert.show = true
                    window.setTimeout(function(){window.location.href = `/portals/time-off/user/${data.result.id}`},1000)
                }
                
            } catch (e) {
                return e;
            }
        },

        async editData() {
            if (JSON.stringify(this.timeoff) === JSON.stringify(this.old_timeoff) & this.newAttachments.length == 0 ) {
                this.editForm = false
                return
            }
            
            isErrorValidate = this.validateData()
            if (isErrorValidate) {
                return
            }

            // make sure not click this twice
            this.editForm = !this.editForm
            this.showButtonEdit = !this.showButtonEdit
            this.alert.message = 'Loading.....'
            this.alert.class =  'alert-secondary'
            this.alert.show = true

            const settings = {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "jsonrpc": "2.0",
                    "params": {
                        "values": {
                            name: this.timeoff.name,
                            employee_id: parseInt(this.timeoff.employee_id),
                            holiday_status_id: parseInt(this.timeoff.holiday_status_id),
                            request_date_from: this.timeoff.request_date_from.toLocaleString(),
                            request_date_to: this.timeoff.request_date_to.toLocaleString(),
                            approver_id : parseInt(this.timeoff.approver_id),
                            pm_leader_id : parseInt(this.timeoff.pm_leader_id),
                            request_date_from_period : this.timeoff.request_date_from_period,
                        },
                        "documents": this.newAttachments,
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_leave/update/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.timeoff = {...this.old_timeoff}
                    // this.newAttachments = []
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                    return
                }
                else {
                    this.editForm = false
                    this.alert.message = data['result']['message']
                    this.alert.class =  'alert-success'
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    
                    // add attachment if exist
                    if (data.result.attachment_ids) {
                        this.newAttachments = []
                        for (let attachment of data.result.attachment_ids) {
                            this.attachments.push({
                                id: attachment[0].id,
                                name: attachment[0].name,
                                file_size: attachment[0].file_size,
                                website_url: attachment[0].website_url
                            })
                        }
                    }
                    
                    // remove alert
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                }
                
            
            } catch (e) {
                return e;
            }
        },
        async action_approve() {
            this.alert.message = 'Loading.....'
            this.alert.class =  'alert-secondary'
            this.alert.show = true

            const settings = {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "jsonrpc": "2.0",
                    "params": {
                        "values": {
                            // check_out : new Date().format('YYYY-MM-DD HH:mm:ss'),
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_leave/approve/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.timeoff = {...this.old_timeoff}
                    // this.newAttachments = []
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                    return
                }
                else {
                    this.editForm = false
                    this.alert.message = data['result']['message']
                    this.alert.class =  'alert-success'
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // remove alert
                    window.setTimeout(function(){window.location.href = `/portals/time-off/approve/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        },

        async deleteAttachment(id){
            let isConfirmed = confirm('Are you sure want to delete this document?')
            if (!isConfirmed) {
                return
            }

            const settings = {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "jsonrpc": "2.0",
                    "params": {
                        
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/ir_attachment/delete/${id}`, settings);
                const data = await fetchResponse.json();
                
                if (data.result.status != 'success') {
                    alert(data.result.message)
                    return
                }
                else {
                    // remove document from documents table
                    this.attachments = this.attachments.filter(x=>x.id != id)
                }

                
            } catch (e) {
                return e;
            }
        },

        async action_reject() {
            console.log(this.timeoff.reject_reason)

            this.alert.message = 'Loading.....'
            this.alert.class =  'alert-secondary'
            this.alert.show = true

            const settings = {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    "jsonrpc": "2.0",
                    "params": {
                        "values": {
                            reject_reason : this.timeoff.reject_reason,
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_leave/reject/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.timeoff = {...this.old_timeoff}
                    // this.newAttachments = []
                    setTimeout(()=>{
                        this.alert.show = false
                    }, 3000);
                    return
                }
                else {
                    this.editForm = false
                    this.alert.message = data['result']['message']
                    this.alert.class =  'alert-success'
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // remove alert
                    window.setTimeout(function(){window.location.href = `/portals/time-off/approve/${data.result.id}`},1000)
                }
            } catch (e) {
                return e;
            }
        },
    });

})