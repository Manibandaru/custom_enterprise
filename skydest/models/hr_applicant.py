
from odoo import fields, models,api,_

class Applicant(models.Model):
    _inherit = "hr.applicant"


    job_number = fields.Text(string='Job Number',website_form_blacklisted="False")
    char_field = fields.Char(string='Test')


    experience = fields.Selection([('0','0-1'),('1','1-2'),('2','2-3'),('3','3-4'),('4','4-5'),('5','5+')],string='Experience')
    education = fields.Selection([('school','School'),('higher_secondary','Higher Secondary'),('diploma','Diploma'),('degree','Degree'),('post_graduate','Post Graduate')],string='Education')
    visa_status=fields.Selection([('student','Student Visa'),('visit','Visit Visa'),('employed','Employment Visa'),('dependent','Depended Visa')],string='Visa Status')
    availability= fields.Selection([('immediate','Immediate'),('10','10 Days'),('20','20 Days'),('30','30 Days')],string='Availability')
    salary_exp = fields.Selection([('no_salary','No Salary'),('1000-2000','1,000 to 2,000'),('2000-3000','2 to 3'),('3000-5000','3 to 5'),('5000-10000','5 to 10'),('10000-15000','10 to 15'),('15000+','15+')],string='Expected Salary')
    nationality = fields.Many2one('res.country',string='Nationality')
    gender = fields.Selection([('male','Male'),('female','Female'),('other','Other')],string='Gender')
    emirate = fields.Selection([
        ('dubai','Dubai'),
        ('sharjah', 'Sharjah'),
        ('ajman', 'Ajman'),
        ('ras_al_kaimah', 'RAK'),
        ('umm_al_quwain', 'UAQ'),
        ('fujairah', 'Fujairah'),
        ('abudhabi', 'Abu Dhabi'),
                ],string='Emirate')
    dob = fields.Date(string='Date of Birth')
    university = fields.Char(string='University')
    course = fields.Char(string='Course of study')
    year_of_study = fields.Char(string='Year of Study')
    intern_role = fields.Selection([('accounts','Accounting or Finance'),('admin','Administration'),('architecture','Architecture'),
                                    ('sales', 'Sales, Marketing and business development'),
                                    ('social', 'Community and Social Services Internships'),
                                    ('consultant', 'Consultant'),
                                    ('customer_service', 'Customer Services and Support'),
                                    ('education', 'Education Internships'),
                                    ('engineering', 'Engineering'),
                                    ('data_analytics', 'Data and Analytics'),
                                    ('animation', 'Design and Animation'),
                                    ('healthcare', 'Healthcare Services'),
                                    ('hr', 'Human Resources'),
                                    ('interior', 'Interior Design'),
                                    ('it', 'IT, Web and Software Development'),
                                    ('legal', 'Legal'),
                                    ('media', 'Media and Communications'),
                                    ('operations', 'Operations'),
                                    ('photography', 'Photography and Videography'),
                                    ('logistics', 'Supply chain and logistics management'),
                                    ('project_management', 'Project Management'),
                                    ('events', 'Promotions and events'),
                                    ('research', 'Research'),
                                    ('journalism', 'Journalism and writing'),






                                    ],string='Internship Role')
    description = fields.Text("Short Bio")

    @api.model
    def create(self, vals):
        if vals.get('department_id') and not self._context.get('default_department_id'):
            self = self.with_context(default_department_id=vals.get('department_id'))
        if vals.get('job_id') or self._context.get('default_job_id'):
            job_id = vals.get('job_id') or self._context.get('default_job_id')
            for key, value in self._onchange_job_id_internal(job_id)['value'].items():
                if key not in vals:
                    vals[key] = value
        if vals.get('user_id'):
            vals['date_open'] = fields.Datetime.now()
        if 'stage_id' in vals:
            vals.update(self._onchange_stage_id_internal(vals.get('stage_id'))['value'])
        if 'email_from' in vals:
            mail_content = "  Hello Your Application is Successfully Submitted . Thank you "
            main_content = {
                'subject': "Application Submitted",
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to':(vals.get('email_from'))
            }

            self.env['mail.mail'].create(main_content).send()
        return super(Applicant, self.with_context(mail_create_nolog=True)).create(vals)





class hr_job_custom(models.Model):
    _inherit = "hr.job"


    job_type = fields.Selection([('job','Job'),('internship','Intern'),('cv_droping','CV Drop In')] ,required=True)
