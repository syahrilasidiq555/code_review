odoo.define('odoo_attendance_user_location.my_attendances', function(require) {
    /**
    * This class is used to get the checkin/out location of employee
    */
    "use strict";
    var MyAttendances = require("hr_attendance.my_attendances");
    var KioskConfirm = require("hr_attendance.kiosk_confirm");
    const session = require("web.session");
    var Dialog = require("web.Dialog");
    var core = require("web.core");
    var field_utils = require('web.field_utils');
    var QWeb = core.qweb;
    
    let latitude;
    let longitude;
    
    MyAttendances.include({
        willStart: function () {
            var self = this;
    
            var def = this._rpc({
                    model: 'hr.employee',
                    method: 'search_read',
                    args: [[['user_id', '=', this.getSession().uid]], ['attendance_state', 'name', 'hours_today']],
                    context: session.user_context,
                })
                .then(function (res) {
                    self.employee = res.length && res[0];
                    if (res.length) {
                        self.hours_today = field_utils.format.float_time(self.employee.hours_today);
                    }
                });
    
            // return Promise.all([def, this._super.apply(this, arguments)]);
            return Promise.all([def, this._super.apply(this, arguments), this.initCoords()]);
        },
        
        initCoords: function() {
            if (navigator.geolocation) {
                this.getGeoLocation();
            } else {
                alert('Browser ini tidak bisa akses lokasi anda, silahkan Accept allow location atau gunakan browser yang lain.');
            }
        },
        
        getGeoLocation: function() {
            navigator.geolocation.getCurrentPosition(this._updateLocation, this._errorHandler, { enableHighAccuracy: true, maximumAge: 60000, timeout: 27000 });
        },

        _updateLocation: function(position) {
            latitude = position.coords.latitude;
            longitude = position.coords.longitude;
        },

        _errorHandler: function(error) {
            // Handle any errors
            if (error) {
                var MyDialog = new Dialog(null, {
                    title: error.__proto__.constructor.name,
                    size: "medium",
                    $content: $('<main/>', {
                        role: 'alert',
                        // text: error['message'] + ". Also check your site connection is secured!",
                        text: "Browser ini tidak bisa akses lokasi anda, silahkan Accept allow location atau gunakan browser yang lain. Detail : \n\n"+error['message'],
                    }),
                    buttons: [{
                        text: "OK",
                        classes: "btn-primary",
                        click: function() {
                            MyDialog.close();
                        }
                    }]
                });
                MyDialog.open();
            }
        },

        update_attendance: function() {
        //To get current position of the employee
            var self = this
                , WebCamDialog = $(QWeb.render("WebCamDialog"))
                , img_data = '';

            this._rpc({
                model: 'hr.employee',
                method: 'get_attendance_state',
                args: [[self.employee.id], ]
            }).then(function(res) {
                if (res == 'checked_out') {
                    Webcam.set({
                        width: 320,
                        height: 240,
                        dest_width: 320,
                        dest_height: 240,
                        image_format: 'jpeg',
                        jpeg_quality: 90,
                        force_flash: false,
                        fps: 45,
                        swfURL: '/hr_attendance/static/src/js/webcam.swf',
                    });
                    var dialog = new Dialog(self,{
                        size: 'large',
                        dialogClass: 'o_act_window',
                        title: "WebCam Booth",
                        $content: WebCamDialog,
                        buttons: [{
                            text: "Capture & Check In",
                            classes: 'btn-primary take_snap_btn',
                            click: function() {
                                Webcam.snap(function(data) {
                                    img_data = data;
                                    $('#live_webcam').hide();
                                    $('#webcam_result').show();
                                    WebCamDialog.find("#webcam_result").html('<img src="' + img_data + '"/>');
                                    // var img_data_base64 = img_data;
                                    var img_data_base64 = img_data.split(',')[1];
                                    if (img_data != '') {
                                        const ctx = Object.assign(session.user_context, {
                                            latitude: latitude,
                                            longitude: longitude,
                                            img_data : img_data_base64
                                        });
                                        self._rpc({
                                            model: 'hr.employee',
                                            method: 'attendance_manual',
                                            args: [
                                            [self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'
                                        ],
                                            context: ctx,
                                        })
                                        .then(function(result) {
                                            if (result.action) {
                                                self.do_action(result.action);
                                            } else if (result.warning) {
                                                self.displayNotification({
                                                    title: result.warning,
                                                    type: 'danger'
                                                });
                                            }
                                        });
                                        close: true
                                    } else if (img_data == '') {
                                        alert("Anda Belum memasukan Photo !");
                                        close: false
                                    }
                                });
                                if (Webcam.live) {
                                    $('.save_close_btn').removeAttr('disabled');
                                }
                            }
                        }, {
                            text: "Close",
                            close: true
                        }]
                    }).open();
                    dialog.opened().then(function() {
                        Webcam.attach('#live_webcam');
                        $('#webcam_result').hide();
                        $('.save_close_btn').attr('disabled', 'disabled');
                        WebCamDialog.find("#webcam_result").html('<img src="/hr_attendance/static/src/img/webcam_placeholder.png"/>');
                    });
                } else {
                    const ctx = Object.assign(session.user_context, {
                        latitude: latitude,
                        longitude: longitude,
                    });
                    self._rpc({
                        model: 'hr.employee',
                        method: 'attendance_manual',
                        args: [
                        [self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'
                    ],
                        context: ctx,
                    })
                    .then(function(result) {
                        if (result.action) {
                            self.do_action(result.action);
                        } else if (result.warning) {
                            self.displayNotification({
                                title: result.warning,
                                type: 'danger'
                            });
                        }
                    });
                }
            })
            


            // if (navigator.geolocation) {
            //     navigator.geolocation.getCurrentPosition(function(position) {
            //             const ctx = Object.assign(session.user_context, {
            //                 latitude: position.coords.latitude,
            //                 longitude: position.coords.longitude,
            //             });
            //             latitude = position.coords.latitude;
            //             longitude = position.coords.longitude;
            //             self._rpc({
            //                     model: 'hr.employee',
            //                     method: 'attendance_manual',
            //                     args: [
            //                     [self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'
            //                 ],
            //                     context: ctx,
            //                 })
            //                 .then(function(result) {
            //                     if (result.action) {
            //                         self.do_action(result.action);
            //                     } else if (result.warning) {
            //                         self.displayNotification({
            //                             title: result.warning,
            //                             type: 'danger'
            //                         });
            //                     }
            //                 });
            //         },
            //         function(error) {
            //             // Handle any errors
            //             if (error) {
            //                 var MyDialog = new Dialog(null, {
            //                     title: error.__proto__.constructor.name,
            //                     size: "medium",
            //                     $content: $('<main/>', {
            //                         role: 'alert',
            //                         // text: error['message'] + ". Also check your site connection is secured!",
            //                         text: "Browser ini tidak bisa akses lokasi anda, silahkan Accept allow location atau gunakan browser yang lain. Detail : \n\n"+error['message'],
            //                     }),
            //                     buttons: [{
            //                         text: "OK",
            //                         classes: "btn-primary",
            //                         click: function() {
            //                             MyDialog.close();
            //                         }
            //                     }]
            //                 });
            //                 MyDialog.open();
            //             }
            //         },
            //         { enableHighAccuracy: true, maximumAge: 60000, timeout: 27000 });
            // } else {
            //     this._rpc({
            //             model: 'hr.employee',
            //             method: 'attendance_manual',
            //             args: [
            //                 [self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'
            //             ],
            //             context: session.user_context,
            //         })
            //         .then(function(result) {
            //             if (result.action) {
            //                 self.do_action(result.action);
            //             } else if (result.warning) {
            //                 self.displayNotification({
            //                     title: result.warning,
            //                     type: 'danger'
            //                 });
            //             }
            //         });
            // }
        },
    });
    KioskConfirm.include({
        events: _.extend(KioskConfirm.prototype.events, {
            "click .o_hr_attendance_sign_in_out_icon": _.debounce(
                function() {
                //  Function to do on clicking sign out
                    var self = this;
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(function(position) {
                                const ctx = Object.assign(session.user_context, {
                                    latitude: position.coords.latitude,
                                    longitude: position.coords.longitude,
                                });
                                latitude = position.coords.latitude;
                                longitude = position.coords.longitude;
                                self._rpc({
                                        model: 'hr.employee',
                                        method: 'attendance_manual',
                                        args: [
                                            [self.employee_id], self.next_action
                                        ],
                                        context: ctx,
                                    })
                                    .then(function(result) {
                                        if (result.action) {
                                            self.do_action(result.action);
                                        } else if (result.warning) {
                                            self.displayNotification({
                                                title: result.warning,
                                                type: 'danger'
                                            });
                                        }
                                    });
                            },
                            function(error) {
                                // Handle any errors
                                if (error) {
                                    var MyDialog = new Dialog(null, {
                                        title: error.__proto__.constructor.name,
                                        size: "medium",
                                        $content: self.$el.find('<main/>', {
                                            role: 'alert',
                                            text: error['message'] + ". Also check your site connection is secured!",
                                        }),
                                        buttons: [{
                                            text: "OK",
                                            classes: "btn-primary",
                                            click: function() {
                                                MyDialog.close();
                                            }
                                        }]
                                    });
                                    MyDialog.open();
                                }
                            });
                    }
                },
                200,
                true
            ),
            "click .o_hr_attendance_pin_pad_button_ok": _.debounce(
                function() {
            //    Pin pad button
                    var self = this;
                    this.pin_pad = true;
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(function(position) {
                                const ctx = Object.assign(session.user_context, {
                                    latitude: position.coords.latitude,
                                    longitude: position.coords.longitude,
                                });
                                latitude = position.coords.latitude;
                                longitude = position.coords.longitude;
                                self._rpc({
                                        model: 'hr.employee',
                                        method: 'attendance_manual',
                                        args: [
                                            [self.employee_id], self.next_action, self.$('.o_hr_attendance_PINbox')
                                            .val()
                                        ],
                                        context: session.user_context,
                                    })
                                    .then(function(result) {
                                        if (result.action) {
                                            self.do_action(result.action);
                                        } else if (result.warning) {
                                            self.displayNotification({
                                                title: result.warning,
                                                type: 'danger'
                                            });
                                            self.$('.o_hr_attendance_PINbox')
                                                .val('');
                                            setTimeout(function() {
                                                self.$('.o_hr_attendance_pin_pad_button_ok')
                                                    .removeAttr("disabled");
                                            }, 500);
                                        }
                                    });
                            },
                            function(error) {
                                // Handle any errors
                                if (error) {
                                    var MyDialog = new Dialog(null, {
                                        title: error.__proto__.constructor.name,
                                        size: "medium",
                                        $content: self.$.el.find('<main/>', {
                                            role: 'alert',
                                            text: error['message'] + ". Also check your site connection is secured!",
                                        }),
                                        buttons: [{
                                            text: "OK",
                                            classes: "btn-primary",
                                            click: function() {
                                                MyDialog.close();
                                            }
                                        }]
                                    });
                                    MyDialog.open();
                                }
                            });
                    }
                },
                200,
                true
            ),
        }),
    });
});
