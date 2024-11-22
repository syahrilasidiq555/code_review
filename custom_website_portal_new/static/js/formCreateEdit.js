document.addEventListener('alpine:init', async () => {
    Alpine.store('expenseStore', {
        active_id : 0,
        expense: {
            name: '',
            product_id: '0',
            date: '',
            unit_amount: '1000',
            quantity: 1,
            expense_location: '0',
            description: '',
            total_amount: 0,
        },
        old_expense : {},
        attachments: [],
        newAttachments:[],
        alert: {
            show: false,
            message: 'ini alert message',
            iconHref: "#check-circle-fill",
            class: 'alert-success',
        },
        editForm: false,
        demaskMoney(value) {
            return value.replaceAll(',', '')
        },
        action_edit(){
            this.old_expense = {...this.expense}
            this.editForm =  true
        },
        action_cancel(){
            if (JSON.stringify(this.expense) === JSON.stringify(this.old_expense) & this.newAttachments.length == 0 ) {
                this.editForm = false
            } else {
                let isConfirmed = confirm('The record has been modified, your changes will be discarded. Do you want to proceed')
                if (isConfirmed) {
                    this.expense = {...this.old_expense}
                    this.editForm = false
                    this.newAttachments = []
                    document.getElementById('documents').value = null;
                }
                
            }
        },
        compute_total_amount() {
            total_amount = this.expense.unit_amount? this.expense.quantity * parseFloat(this.demaskMoney(this.expense.unit_amount)) : 0
            this.expense.total_amount = parseFloat(total_amount).toFixed(2)
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
                this.attachments = this.attachments.filter(x=>x.id != id)
                
            } catch (e) {
                return e;
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
            if (!this.expense.name) {
                this.alert.show = true
                this.alert.message = 'Title must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!parseInt(this.expense.product_id)) {
                this.alert.show = true
                this.alert.message = 'Product must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (parseInt(this.expense.unit_amount) < 1 | parseInt(this.expense.quantity) < 1) {
                this.alert.show = true
                this.alert.message = 'Unit Amount or Quantity must be more than 0!'
                this.alert.class = 'alert-danger'
                return true
            }
            if (!parseInt(this.expense.expense_location)) {
                this.alert.show = true
                this.alert.message = 'Location must be filled!'
                this.alert.class = 'alert-danger'
                return true
            }

        },

        async submitData() {
            if (JSON.stringify(this.expense) === JSON.stringify(this.old_expense) & this.newAttachments.length == 0 ) {
                this.editForm = false
                return
            }
            // console.log(this.expense)
            isErrorValidate = this.validateData()
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
                            name : this.expense.name,
                            product_id : parseInt(this.expense.product_id) > 0 ? parseInt(this.expense.product_id) : false,
                            date : this.expense.date,
                            unit_amount : parseFloat(this.demaskMoney(this.expense.unit_amount)),
                            quantity : parseInt(this.expense.quantity),
                            expense_location : parseInt(this.expense.expense_location) > 0 ? parseInt(this.expense.expense_location) : false,
                            // expense_location : 0,
                            description : this.expense.description,
                            // documents : this.expense.documents,
                        },
                        "documents": this.newAttachments
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_expense/update/${this.active_id}`, settings);
                const data = await fetchResponse.json();
                this.editForm = false
                this.alert.message = data['result']['message']
                this.alert.class =  'alert-success'
                this.alert.show = true
                
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
            
            } catch (e) {
                return e;
            }
        },
        async getTransactions() {
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
                const fetchResponse = await fetch(`/portals/hr_expense/search`, settings);
                const data = await fetchResponse.json();
                console.log(data)
                
            } catch (e) {
                return e;
            }
        },
        async createData(){
            this.getTransactions()
            return
            // console.log(this.expense)
            // console.log(this.newAttachments)
            isErrorValidate = this.validateData()
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
                            name : this.expense.name,
                            product_id : parseInt(this.expense.product_id) > 0 ? parseInt(this.expense.product_id) : false,
                            date : this.expense.date,
                            unit_amount : parseFloat(this.demaskMoney(this.expense.unit_amount)),
                            quantity : parseInt(this.expense.quantity),
                            expense_location : parseInt(this.expense.expense_location) > 0 ? parseInt(this.expense.expense_location) : false,
                            // expense_location : 0,
                            description : this.expense.description,
                            // documents : this.expense.documents,
                        },
                        "documents": this.newAttachments
                    }
                })
            };

            try {
                const fetchResponse = await fetch(`/portals/hr_expense/create`, settings);
                const data = await fetchResponse.json();
                console.log(data)
                this.editForm = !this.editForm
                this.alert.message = data['result']['message']
                this.alert.class =  'alert-success'
                this.alert.show = true
                window.setTimeout(function(){window.location.href = `/portals/expense/${data.result.id}`},1000)
                // console.log("data")
                
            } catch (e) {
                return e;
            }
        }
    });

})