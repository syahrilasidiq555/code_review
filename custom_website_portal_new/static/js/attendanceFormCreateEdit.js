document.addEventListener('alpine:init', async () => {
    Alpine.store('attendanceStore', {
        active_id : 0,
        attendance: {
            employee_id: '',
            attendance_type: '',
            attendance_type_id: '',
            partner_id: '',
            task: '',
            description: '',
            approver_id: '',
            pm_leader_id: '',
            location_id: '',
            check_in: '',
            check_out: '',
            worked_hours: '',
            reject_reason: '',
            state: 'draft',
        },
        old_attendance : {},
        alert: {
            show: false,
            message: 'ini alert message',
            iconHref: "#check-circle-fill",
            class: 'alert-success',
        },
        editForm: false,
        showButtonEdit:true,

        demaskMoney(value) {
            return value.replaceAll(',', '')
        },
        action_edit(){
            this.old_attendance = {...this.attendance}
            this.editForm =  true
        },
        action_cancel(){
            if (!this.active_id) {
                // cancel dalam create mode
                let isConfirmed = confirm('The record has been modified, your changes will be discarded. Do you want to proceed')
                if (isConfirmed) {
                    window.setTimeout(function(){window.location.href = `/portals/attendance`},500)
                }
            } else {
                // cancel dalam edit mode
                this.alert.show = false
                if (JSON.stringify(this.attendance) === JSON.stringify(this.old_attendance)) {
                    this.editForm = false
                } else {
                    let isConfirmed = confirm('The record has been modified, your changes will be discarded. Do you want to proceed')
                    if (isConfirmed) {
                        this.attendance = {...this.old_attendance}
                        this.editForm = false
                        document.getElementById('documents').value = null;
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
            // if (this.attendance.type == '0') {
            //     this.alert.show = true
            //     this.alert.message = 'Type must be choosed!'
            //     this.alert.class = 'alert-danger'
            //     return true
            // }
            if (!parseInt(this.attendance.attendance_type_id)) {
                this.alert.show = true
                this.alert.message = 'Attendance Type must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!this.attendance.task) {
                this.alert.show = true
                this.alert.message = 'Task must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!this.attendance.description) {
                this.alert.show = true
                this.alert.message = 'Description must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }
            // if (!this.working_at_home && !parseInt(this.attendance.partner_id)) {
            //     this.alert.show = true
            //     this.alert.message = 'Project Customer must be choosed!'
            //     this.alert.class = 'alert-danger'
            //     return true
            // }
            if (!parseInt(this.attendance.approver_id)) {
                this.alert.show = true
                this.alert.message = 'Approver must be choosed!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!parseInt(this.attendance.pm_leader_id)) {
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

        validateApprove(){
            this.alert.show = false
            if (!this.attendance.check_in) {
                this.alert.show = true
                this.alert.message = 'Check In Date must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!this.attendance.check_out) {
                this.alert.show = true
                this.alert.message = 'Check Out Date must be filled!'
                this.alert.class = 'alert-danger'
                return true
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
                            employee_id : parseInt(this.attendance.employee_id),
                            attendance_type : '', 
                            attendance_type_id : parseInt(this.attendance.attendance_type_id),
                            partner_id : parseInt(this.attendance.partner_id),
                            task : this.attendance.task,
                            description : this.attendance.description,
                            approver_id : parseInt(this.attendance.approver_id),
                            pm_leader_id : parseInt(this.attendance.pm_leader_id),
                            location_id : parseInt(this.attendance.location_id),
                            // check_in : this.attendance.check_in,
                            // check_out : this.attendance.check_out,
                            // worked_hours : this.attendance.worked_hours,
                            // state : this.attendance.state,
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_attendance/create`, settings);
                const data = await fetchResponse.json();
                // console.log(data)
                if (data.result.status != 'success') {
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.editForm = false
                    return
                }
                else {
                    // this.editForm = !this.editForm
                    this.alert.message = data['result']['message']
                    this.alert.class =  'alert-success'
                    this.alert.show = true
                    window.setTimeout(function(){window.location.href = `/portals/attendance/${data.result.id}`},1000)
                }
                
            } catch (e) {
                return e;
            }
        },
        async editData() {
            if (JSON.stringify(this.attendance) === JSON.stringify(this.old_attendance)) {
                this.editForm = false
                return
            }
            // console.log(this.attendance)
            isErrorValidate = this.validateData()
            if (isErrorValidate) {
                return
            }

            console.log("partner id down below :")
            console.log(this.attendance.partner_id)

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
                            employee_id : parseInt(this.attendance.employee_id),
                            attendance_type : '', 
                            attendance_type_id : parseInt(this.attendance.attendance_type_id),
                            partner_id : parseInt(this.attendance.partner_id),
                            task : this.attendance.task,
                            description : this.attendance.description,
                            approver_id : parseInt(this.attendance.approver_id),
                            pm_leader_id : parseInt(this.attendance.pm_leader_id),
                            location_id : parseInt(this.attendance.location_id),
                            check_in : this.attendance.check_in.toLocaleString(),
                            check_out : this.attendance.check_out.toLocaleString(),
                            // worked_hours : this.attendance.worked_hours,
                            // state : this.attendance.state,
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_attendance/update/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.attendance = {...this.old_attendance}
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
                    window.setTimeout(function(){window.location.href = `/portals/attendance/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        },
        async editDataFromApprover() {
            if (JSON.stringify(this.attendance) === JSON.stringify(this.old_attendance)) {
                this.editForm = false
                return
            }
            // console.log(this.attendance)
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
                            employee_id : parseInt(this.attendance.employee_id),
                            attendance_type : '', 
                            attendance_type_id : parseInt(this.attendance.attendance_type_id),
                            partner_id : parseInt(this.attendance.partner_id),
                            task : this.attendance.task,
                            description : this.attendance.description,
                            approver_id : parseInt(this.attendance.approver_id),
                            pm_leader_id : parseInt(this.attendance.pm_leader_id),
                            location_id : parseInt(this.attendance.location_id),
                            check_in : this.attendance.check_in.toLocaleString(),
                            check_out : this.attendance.check_out.toLocaleString(),
                            // worked_hours : this.attendance.worked_hours,
                            // state : this.attendance.state,
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_attendance/update/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.attendance = {...this.old_attendance}
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
                    window.setTimeout(function(){window.location.href = `/portals/attendance_approve/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        },
        async action_checkout() {
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
                const fetchResponse = await fetch(`/portals/hr_attendance/check_out/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.attendance = {...this.old_attendance}
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
                    window.setTimeout(function(){window.location.href = `/portals/attendance/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        },
        async action_checkin() {
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
                const fetchResponse = await fetch(`/portals/hr_attendance/check_in/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.attendance = {...this.old_attendance}
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
                    window.setTimeout(function(){window.location.href = `/portals/attendance/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        },
        async action_approve() {
            isErrorValidate = this.validateApprove()
            if (isErrorValidate) {
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
                        "values": {
                            // check_out : new Date().format('YYYY-MM-DD HH:mm:ss'),
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_attendance/approve/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.attendance = {...this.old_attendance}
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
                    window.setTimeout(function(){window.location.href = `/portals/attendance_approve/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        },
        async action_reject() {
            console.log(this.attendance.reject_reason)
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
                            reject_reason : this.attendance.reject_reason,
                        },
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_attendance/reject/${this.active_id}`, settings);
                const data = await fetchResponse.json();

                if (data.result.status != 'success') {
                    this.editForm = false
                    this.alert.class =  'alert-danger'
                    this.alert.message = data.result.message
                    this.alert.show = true
                    this.showButtonEdit = !this.showButtonEdit
                    // this.attendance = {...this.old_attendance}
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
                    window.setTimeout(function(){window.location.href = `/portals/attendance_approve/${data.result.id}`},1000)
                }
                
            
            } catch (e) {
                return e;
            }
        }
        // async deleteAttachment(id){
        //     let isConfirmed = confirm('Are you sure want to delete this document?')
        //     if (!isConfirmed) {
        //         return
        //     }

        //     const settings = {
        //         method: 'POST',
        //         headers: {
        //             'Accept': 'application/json',
        //             'Content-Type': 'application/json',
        //         },
        //         body: JSON.stringify({
        //             "jsonrpc": "2.0",
        //             "params": {
                        
        //             }
        //         })
        //     };

        //     try {
        //         const fetchResponse = await fetch(`/portals/ir_attachment/delete/${id}`, settings);
        //         const data = await fetchResponse.json();
                
        //         if (data.result.status != 'success') {
        //             alert(data.result.message)
        //             return
        //         }
        //         else {
        //             // remove document from documents table
        //             this.attachments = this.attachments.filter(x=>x.id != id)
        //         }

                
        //     } catch (e) {
        //         return e;
        //     }
        // },
    });

})