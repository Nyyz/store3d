from django import forms
from api.models import CustomUser

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'country']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Паролі не співпадають.")
        return cleaned_data

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True, error_messages={'required': "Ім'я обов'язкове."})
    last_name = forms.CharField(max_length=50, required=True, error_messages={'required': "Прізвище обов'язкове."})
    phone = forms.CharField(max_length=20, required=True, error_messages={'required': "Телефон обов'язковий."})
    email = forms.EmailField(required=True, error_messages={'required': "Email обов'язковий."})
    
    delivery_service = forms.ChoiceField(
        choices=[('nova_poshta', 'Nova Poshta'), ('ppl', 'PPL'), ('meest', 'Meest')],
        required=True
    )
    payment_method = forms.ChoiceField(
        choices=[('bank', 'Bank Transfer'), ('card', 'Credit Card'), ('paypal', 'PayPal'), ('cod', 'Cash on Delivery')],
        required=True
    )
    
    # Nova Poshta fields
    np_city = forms.CharField(max_length=100, required=False)
    np_city_ref = forms.CharField(max_length=100, required=False)
    np_warehouse = forms.CharField(max_length=200, required=False)
    np_warehouse_ref = forms.CharField(max_length=100, required=False)
    
    # PPL fields
    ppl_city = forms.CharField(max_length=100, required=False)
    ppl_point = forms.CharField(max_length=200, required=False)
    
    # Meest fields
    meest_country = forms.CharField(max_length=100, required=False)
    meest_city = forms.CharField(max_length=100, required=False)
    meest_address = forms.CharField(max_length=255, required=False)
    
    comment = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super().clean()
        delivery_service = cleaned_data.get("delivery_service")
        
        if delivery_service == 'nova_poshta':
            if not cleaned_data.get('np_city'):
                self.add_error('np_city', "Місто обов'язкове для Нової Пошти.")
            if not cleaned_data.get('np_warehouse'):
                self.add_error('np_warehouse', "Відділення обов'язкове для Нової Пошти.")
        elif delivery_service == 'ppl':
            if not cleaned_data.get('ppl_city'):
                self.add_error('ppl_city', "Місто обов'язкове для PPL.")
            if not cleaned_data.get('ppl_point'):
                self.add_error('ppl_point', "Відділення обов'язкове для PPL.")
        elif delivery_service == 'meest':
            if not cleaned_data.get('meest_country'):
                self.add_error('meest_country', "Країна обов'язкова для Meest.")
            if not cleaned_data.get('meest_city'):
                self.add_error('meest_city', "Місто обов'язкове для Meest.")
            if not cleaned_data.get('meest_address'):
                self.add_error('meest_address', "Адреса обов'язкова для Meest.")
                
        return cleaned_data
