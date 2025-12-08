frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        // Add button to fetch shift advances
        if (!frm.is_new() && frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
            frm.add_custom_button(__('Fetch Shift Advances'), function() {
                frappe.call({
                    method: 'petrodiesel.petrodiesel.custom.salary_slip_custom.fetch_shift_advances',
                    args: {
                        doc: frm.doc
                    },
                    callback: function(r) {
                        frm.reload_doc();
                        frappe.msgprint(__('Shift advances fetched successfully'));
                    }
                });
            });
        }
        
        // Show total advances prominently
        if (frm.doc.total_shift_advances && frm.doc.total_shift_advances > 0) {
            frm.dashboard.add_indicator(__('Shift Advances: {0}', 
                [format_currency(frm.doc.total_shift_advances)]), 
                'orange');
        }
    },
    
    employee: function(frm) {
        // Auto-fetch when employee changes
        if (frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
            fetch_advances(frm);
        }
    },
    
    start_date: function(frm) {
        if (frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
            fetch_advances(frm);
        }
    },
    
    end_date: function(frm) {
        if (frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
            fetch_advances(frm);
        }
    }
});

function fetch_advances(frm) {
    // This triggers the before_save hook
    frm.save();
}
