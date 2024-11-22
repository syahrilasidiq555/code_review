{
    "name":"Performance Appraisal",
    "version": "15.0.1.1.1",
    "category":"Custom Module",
    "description": """
        Performance Appraisal
    """,
    "depends":[
        "base",
        "mail",
        "hr",
    ],
    "data":[   
        "security/group.xml",
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "data/performance_appraisal_job_classification.xml",
        "data/ir_cron.xml",
        "views/dym_performance_appraisal_form_b_view.xml",
        "views/dym_performance_appraisal_form_a_view.xml",
        "views/performance_appraisal_job_classification.xml",  
        # "security/dym_performance_appraisal_view.xml",
        "wizard/report_performance_atasan1_done_wizard_view.xml",
        "wizard/report_performance_employee_atasan1_wizard_view.xml",
        "wizard/report_performance_belum_employee_wizard_view.xml",
        'report/report_performance_appraisal.xml',
        
    ],
    "active":False,
    "installable":True,
}