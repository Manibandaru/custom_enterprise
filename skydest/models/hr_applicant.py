
from odoo import fields, models,api,_

class Applicant(models.Model):
    _inherit = "hr.applicant"


    job_number = fields.Text(string='Job Number',website_form_blacklisted="False")
    char_field = fields.Char(string='Test')


    experience = fields.Selection([('0','0-1'),('1','1-2'),('2','2-3'),('3','3-4'),('4','4-5'),('5','5+')],string='Experience')
    education = fields.Selection([('school','School'),('higher_secondary','Higher Secondary'),('diplamo','Diploma'),('degree','Degree'),('post_graduate','Post Graduate')],string='Education')
    visa_status=fields.Selection([('visit','Visit Visa'),('employed','Employment Visa'),('dependent','Depended Visa')],string='Visa Status')
    availability= fields.Selection([('immediate','Immediate'),('10','10 Days'),('20','20 Days'),('30','30 Days')],string='Availability')
    salary_exp = fields.Selection([('1000-2000','1,000 to 2,000'),('2000-3000','2 to 3'),('3000-5000','3 to 5'),('5000-10000','5 to 10'),('10000-15000','10 to 15'),('15000+','15+')],string='Expected Salary')
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
