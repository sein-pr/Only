# forms/profile_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Email, Length

# Country code choices for phone numbers
COUNTRY_CODES = [
    ('+1', '+1 (US/Canada)'),
    ('+44', '+44 (UK)'),
    ('+91', '+91 (India)'),
    ('+86', '+86 (China)'),
    ('+81', '+81 (Japan)'),
    ('+49', '+49 (Germany)'),
    ('+33', '+33 (France)'),
    ('+39', '+39 (Italy)'),
    ('+34', '+34 (Spain)'),
    ('+61', '+61 (Australia)'),
    ('+55', '+55 (Brazil)'),
    ('+7', '+7 (Russia)'),
    ('+82', '+82 (South Korea)'),
    ('+65', '+65 (Singapore)'),
    ('+60', '+60 (Malaysia)'),
    ('+66', '+66 (Thailand)'),
    ('+63', '+63 (Philippines)'),
    ('+62', '+62 (Indonesia)'),
    ('+84', '+84 (Vietnam)'),
    ('+27', '+27 (South Africa)'),
    ('+20', '+20 (Egypt)'),
    ('+234', '+234 (Nigeria)'),
    ('+254', '+254 (Kenya)'),
    ('+233', '+233 (Ghana)'),
    ('+212', '+212 (Morocco)'),
    ('+213', '+213 (Algeria)'),
    ('+216', '+216 (Tunisia)'),
    ('+218', '+218 (Libya)'),
    ('+220', '+220 (Gambia)'),
    ('+221', '+221 (Senegal)'),
    ('+222', '+222 (Mauritania)'),
    ('+223', '+223 (Mali)'),
    ('+224', '+224 (Guinea)'),
    ('+225', '+225 (Ivory Coast)'),
    ('+226', '+226 (Burkina Faso)'),
    ('+227', '+227 (Niger)'),
    ('+228', '+228 (Togo)'),
    ('+229', '+229 (Benin)'),
    ('+230', '+230 (Mauritius)'),
    ('+231', '+231 (Liberia)'),
    ('+232', '+232 (Sierra Leone)'),
    ('+235', '+235 (Chad)'),
    ('+236', '+236 (Central African Republic)'),
    ('+237', '+237 (Cameroon)'),
    ('+238', '+238 (Cape Verde)'),
    ('+239', '+239 (São Tomé and Príncipe)'),
    ('+240', '+240 (Equatorial Guinea)'),
    ('+241', '+241 (Gabon)'),
    ('+242', '+242 (Republic of the Congo)'),
    ('+243', '+243 (Democratic Republic of the Congo)'),
    ('+244', '+244 (Angola)'),
    ('+245', '+245 (Guinea-Bissau)'),
    ('+246', '+246 (British Indian Ocean Territory)'),
    ('+248', '+248 (Seychelles)'),
    ('+249', '+249 (Sudan)'),
    ('+250', '+250 (Rwanda)'),
    ('+251', '+251 (Ethiopia)'),
    ('+252', '+252 (Somalia)'),
    ('+253', '+253 (Djibouti)'),
    ('+255', '+255 (Tanzania)'),
    ('+256', '+256 (Uganda)'),
    ('+257', '+257 (Burundi)'),
    ('+258', '+258 (Mozambique)'),
    ('+260', '+260 (Zambia)'),
    ('+261', '+261 (Madagascar)'),
    ('+262', '+262 (Réunion)'),
    ('+263', '+263 (Zimbabwe)'),
    ('+264', '+264 (Namibia)'),
    ('+265', '+265 (Malawi)'),
    ('+266', '+266 (Lesotho)'),
    ('+267', '+267 (Botswana)'),
    ('+268', '+268 (Swaziland)'),
    ('+269', '+269 (Comoros)'),
    ('+290', '+290 (Saint Helena)'),
    ('+291', '+291 (Eritrea)'),
    ('+297', '+297 (Aruba)'),
    ('+298', '+298 (Faroe Islands)'),
    ('+299', '+299 (Greenland)'),
    ('+350', '+350 (Gibraltar)'),
    ('+351', '+351 (Portugal)'),
    ('+352', '+352 (Luxembourg)'),
    ('+353', '+353 (Ireland)'),
    ('+354', '+354 (Iceland)'),
    ('+355', '+355 (Albania)'),
    ('+356', '+356 (Malta)'),
    ('+357', '+357 (Cyprus)'),
    ('+358', '+358 (Finland)'),
    ('+359', '+359 (Bulgaria)'),
    ('+370', '+370 (Lithuania)'),
    ('+371', '+371 (Latvia)'),
    ('+372', '+372 (Estonia)'),
    ('+373', '+373 (Moldova)'),
    ('+374', '+374 (Armenia)'),
    ('+375', '+375 (Belarus)'),
    ('+376', '+376 (Andorra)'),
    ('+377', '+377 (Monaco)'),
    ('+378', '+378 (San Marino)'),
    ('+380', '+380 (Ukraine)'),
    ('+381', '+381 (Serbia)'),
    ('+382', '+382 (Montenegro)'),
    ('+383', '+383 (Kosovo)'),
    ('+385', '+385 (Croatia)'),
    ('+386', '+386 (Slovenia)'),
    ('+387', '+387 (Bosnia and Herzegovina)'),
    ('+389', '+389 (North Macedonia)'),
    ('+420', '+420 (Czech Republic)'),
    ('+421', '+421 (Slovakia)'),
    ('+423', '+423 (Liechtenstein)'),
    ('+500', '+500 (Falkland Islands)'),
    ('+501', '+501 (Belize)'),
    ('+502', '+502 (Guatemala)'),
    ('+503', '+503 (El Salvador)'),
    ('+504', '+504 (Honduras)'),
    ('+505', '+505 (Nicaragua)'),
    ('+506', '+506 (Costa Rica)'),
    ('+507', '+507 (Panama)'),
    ('+508', '+508 (Saint Pierre and Miquelon)'),
    ('+509', '+509 (Haiti)'),
    ('+590', '+590 (Guadeloupe)'),
    ('+591', '+591 (Bolivia)'),
    ('+592', '+592 (Guyana)'),
    ('+593', '+593 (Ecuador)'),
    ('+594', '+594 (French Guiana)'),
    ('+595', '+595 (Paraguay)'),
    ('+596', '+596 (Martinique)'),
    ('+597', '+597 (Suriname)'),
    ('+598', '+598 (Uruguay)'),
    ('+599', '+599 (Netherlands Antilles)'),
    ('+670', '+670 (East Timor)'),
    ('+672', '+672 (Antarctica)'),
    ('+673', '+673 (Brunei)'),
    ('+674', '+674 (Nauru)'),
    ('+675', '+675 (Papua New Guinea)'),
    ('+676', '+676 (Tonga)'),
    ('+677', '+677 (Solomon Islands)'),
    ('+678', '+678 (Vanuatu)'),
    ('+679', '+679 (Fiji)'),
    ('+680', '+680 (Palau)'),
    ('+681', '+681 (Wallis and Futuna)'),
    ('+682', '+682 (Cook Islands)'),
    ('+683', '+683 (Niue)'),
    ('+684', '+684 (American Samoa)'),
    ('+685', '+685 (Samoa)'),
    ('+686', '+686 (Kiribati)'),
    ('+687', '+687 (New Caledonia)'),
    ('+688', '+688 (Tuvalu)'),
    ('+689', '+689 (French Polynesia)'),
    ('+690', '+690 (Tokelau)'),
    ('+691', '+691 (Micronesia)'),
    ('+692', '+692 (Marshall Islands)'),
    ('+850', '+850 (North Korea)'),
    ('+852', '+852 (Hong Kong)'),
    ('+853', '+853 (Macau)'),
    ('+855', '+855 (Cambodia)'),
    ('+856', '+856 (Laos)'),
    ('+880', '+880 (Bangladesh)'),
    ('+886', '+886 (Taiwan)'),
    ('+960', '+960 (Maldives)'),
    ('+961', '+961 (Lebanon)'),
    ('+962', '+962 (Jordan)'),
    ('+963', '+963 (Syria)'),
    ('+964', '+964 (Iraq)'),
    ('+965', '+965 (Kuwait)'),
    ('+966', '+966 (Saudi Arabia)'),
    ('+967', '+967 (Yemen)'),
    ('+968', '+968 (Oman)'),
    ('+970', '+970 (Palestine)'),
    ('+971', '+971 (United Arab Emirates)'),
    ('+972', '+972 (Israel)'),
    ('+973', '+973 (Bahrain)'),
    ('+974', '+974 (Qatar)'),
    ('+975', '+975 (Bhutan)'),
    ('+976', '+976 (Mongolia)'),
    ('+977', '+977 (Nepal)'),
    ('+992', '+992 (Tajikistan)'),
    ('+993', '+993 (Turkmenistan)'),
    ('+994', '+994 (Azerbaijan)'),
    ('+995', '+995 (Georgia)'),
    ('+996', '+996 (Kyrgyzstan)'),
    ('+998', '+998 (Uzbekistan)')
]

class ProfileForm(FlaskForm):
    # Personal Information
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    # Phone fields (new structured approach)
    phone_country_code = SelectField('Country Code', choices=COUNTRY_CODES, validators=[Length(max=5)])
    phone_number = StringField('Phone Number', validators=[Length(max=15)])
    
    # Address fields (new structured approach)
    address_line1 = StringField('Address Line 1', validators=[Length(max=100)])
    address_line2 = StringField('Address Line 2', validators=[Length(max=100)])
    city = StringField('City', validators=[Length(max=50)])
    state_province = StringField('State/Province', validators=[Length(max=50)])
    postal_code = StringField('Postal Code', validators=[Length(max=20)])
    country = StringField('Country', validators=[Length(max=50)])
    
    # Legacy fields (keep for backward compatibility)
    phone = StringField('Phone', validators=[Length(max=20)])
    address = TextAreaField('Address')
    
    avatar = FileField('Profile Avatar')
    
    # Company Information (for sellers)
    company_name = StringField('Company Name', validators=[Length(max=100)])
    company_description = TextAreaField('Company Description')
    company_website = StringField('Website', validators=[Length(max=200)])
    
    # Company phone fields (new structured approach)
    company_phone_country_code = SelectField('Company Country Code', choices=COUNTRY_CODES, validators=[Length(max=5)])
    company_phone_number = StringField('Company Phone Number', validators=[Length(max=15)])
    
    # Company address fields (new structured approach)
    company_address_line1 = StringField('Company Address Line 1', validators=[Length(max=100)])
    company_address_line2 = StringField('Company Address Line 2', validators=[Length(max=100)])
    company_city = StringField('Company City', validators=[Length(max=50)])
    company_state_province = StringField('Company State/Province', validators=[Length(max=50)])
    company_postal_code = StringField('Company Postal Code', validators=[Length(max=20)])
    company_country = StringField('Company Country', validators=[Length(max=50)])
    
    # Legacy company fields (keep for backward compatibility)
    company_phone = StringField('Company Phone', validators=[Length(max=20)])
    company_address = TextAreaField('Company Address')
    
    company_logo = FileField('Company Logo')
