#-*- coding: utf-8 -*-
'''
Created on Mar 22, 2011

@author: jesus
''' 
from django import forms
from django.forms.widgets import Widget
from comerciax.admincomerciax.models import *
from comerciax.utils import fecha_hoy, fecha_hoy_mas_tresanyos

class FGrupo(forms.Form):
    nombre   = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':80}))

class Myregister_user(forms.Form):
    nombre   = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':30}))
    apellidos = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':30}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':30}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class':'required email'}) )
    password = forms.CharField(label='Clave', widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    conpassword = forms.CharField(label='Confirmar clave', widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    
class FEdit_user(forms.Form):
    nombre   = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':30}))
    apellidos = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':30}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':30}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class':'required email'}) )
    
class FChange_password(forms.Form):    
    clave_actual = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    clave_nueva = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    confirmar_clave = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    
class FChange_passwordadm(forms.Form):    
#    clave_actual = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    clave_nueva = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))
    confirmar_clave = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required', 'maxlength':128}))    
    
class Provincia(forms.Form):
    provincia = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':20}) )
    
class FOrganismo(forms.Form):
    codigo = forms.CharField(label='Código',widget=forms.TextInput(attrs={'class':'required', 'maxlength':3}) )
    siglas = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    
class FUnion(forms.Form):
    union = forms.CharField(label='Unión',widget=forms.TextInput(attrs={'class':'required', 'maxlength':20}) )
    
class FSucursal(forms.Form):
    sucursal = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':15}) )

class FArea(forms.Form):
    area = forms.CharField(label='Área', widget=forms.TextInput(attrs={'class':'required', 'maxlength':25}) )
    
class FCausar(forms.Form):
    causa = forms.CharField(widget=forms.Textarea(attrs={'class':'required', 'maxlength':250}) )
    
class FUnidadm(forms.Form):
    unidad = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':5}) )
    
class FFormasp(forms.Form):
    forma = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':25}) )
    
class FMoneda(forms.Form):
    moneda = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':10}) )

class FProducto(forms.Form):
    producto = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    codigo = forms.CharField(label='Código',widget=forms.TextInput(attrs={'class':'required', 'maxlength':18}) )
    precio_mn = forms.DecimalField(label='Precio CUP', widget=forms.TextInput(attrs={'class':'required number', 'max_digits':7, 'decimal_places':2}) )
    precio_cuc = forms.DecimalField(label='Precio MLC', widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    precio_costo_cuc = forms.DecimalField(label='Precio Costo MLC',widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    precio_costo_mn = forms.DecimalField(label='Precio CUP',widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    precio_particular = forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    precio_externo = forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    precio_casco = forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    precio_regrabable = forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    otro_precio_casco = forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number', 'max_digits':7, 'decimal_places':2}))

    precio_vulca = forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    unidad_medida = forms.ModelChoiceField(Umedida.objects.all(),widget=forms.Select(attrs={'class': 'required'}))

class FEmpresa(forms.Form):
    codigo = forms.CharField(label='Código', widget=forms.TextInput(attrs={'class':'required', 'maxlength':14}) )
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}) )
    direccion = forms.CharField(label='Dirección', widget=forms.TextInput(attrs={'class':'required', 'maxlength':200}) )
    email = forms.EmailField(required=False, widget=forms.TextInput(attrs={'class':'email'}) )
    telefono = forms.CharField(label='Teléfono', widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}) )
    fax = forms.CharField(required=False, widget=forms.TextInput(attrs={'maxlength':50}) )
    provincia = forms.ModelChoiceField(Provincias.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    titular_mn = forms.CharField(label='Titular CUP', widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    titular_usd = forms.CharField(label='Titular MLC', widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    cuenta_mn = forms.CharField(label='Cuenta CUP', widget=forms.TextInput(attrs={'class':'required', 'maxlength':19}) )
    cuenta_usd = forms.CharField(label='Cuenta MLC', widget=forms.TextInput(attrs={'class':'required', 'maxlength':19}) )
    sucursal_mn = forms.ModelChoiceField(Sucursales.objects.all(),label='Sucursal CUP',widget=forms.Select(attrs={'class': 'required'}))
    sucursal_usd = forms.ModelChoiceField(Sucursales.objects.all(),label='Sucursal MLC', widget=forms.Select(attrs={'class': 'required'}))
    
class FCliente(forms.Form):
    codigo = forms.CharField(label='Código', widget=forms.TextInput(attrs={'class':'required', 'maxlength':14}) )
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}) )
    direccion = forms.CharField(label='Dirección', widget=forms.TextInput(attrs={'class':'required', 'maxlength':200}) )
    email = forms.EmailField(required=False,widget=forms.TextInput(attrs={'class':'email'}) )
    telefono = forms.CharField(label='Teléfono',required=False, widget=forms.TextInput(attrs={'maxlength':50}) )
    fax = forms.CharField(required=False,widget=forms.TextInput(attrs={'maxlength':50}) )
    provincia = forms.ModelChoiceField(Provincias.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    organismo = forms.ModelChoiceField(Organismo.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    union = forms.ModelChoiceField(label='Unión', required=False,queryset=Union.objects.all(),widget=forms.Select(attrs={'class': 'required','disabled':'disabled'}))
    comercializadora = forms.BooleanField(required=False)
    externo = forms.BooleanField(required=False)
    
    def __init__(self,*args, **kwargs):
        super(FCliente, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            ar = args[0].has_key('organismo')
            idorgg = args[0]['organismo']
            self.fields["union"].queryset = Union.objects.select_related().filter(organismo=Organismo.objects.get(id = idorgg))
        
        if len(kwargs)>0:
            #kwargs['initial'].has_key('organismo')
            siglas = kwargs['initial']['organismo']
            #self.fields["union"].queryset = Union.objects.select_related().filter(organismo=Organismo.objects.get(siglas_organismo = siglas))
            #self.fields["union"].widget = forms.Select(attrs={'class': 'required'})
            queryset2=Union.objects.select_related().filter(organismo=Organismo.objects.get(siglas_organismo = siglas))
            if len(queryset2)>0:
                self.fields["union"] = forms.ModelChoiceField(required=False,queryset=queryset2,widget=forms.Select(attrs={'class': 'required'}))
            else:
                self.fields["union"] = forms.ModelChoiceField(required=False,queryset=queryset2,widget=forms.Select(attrs={'disabled': 'disabled'}))
    
class FContrato(forms.Form):
    contrato_nro = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':10}) )
    fecha_vigencia=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    tiempo_vigencia=forms.IntegerField(label='Vigencia(años)',widget=forms.TextInput(attrs={'class':'required digits','min':1, 'value':3}))
    fecha_vencimiento=forms.DateField(required = True, widget=forms.DateInput(attrs={'value':fecha_hoy_mas_tresanyos(),'readonly':True}))
#    plan_contratado = forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits','min':0}))
    sucursal_mn = forms.ModelChoiceField(Sucursales.objects.all(),label='Sucursal CUP',widget=forms.Select(attrs={'class': 'required'}))
    cuenta_mn = forms.CharField(label='Cuenta CUP',widget=forms.TextInput(attrs={'class':'required', 'maxlength':19}) )
    titular_mn = forms.CharField(label='Títular CUP', widget=forms.TextInput(attrs={'class':'required', 'maxlength':80}) )
    sucursal_usd = forms.ModelChoiceField(Sucursales.objects.all(),label='Sucursal MLC',required = False, widget=forms.Select())
    cuenta_usd = forms.CharField(label='Cuenta MLC',required = False,widget=forms.TextInput(attrs={'maxlength':19}) )
    titular_usd = forms.CharField(label='Títular MLC',required = False, widget=forms.TextInput(attrs={'maxlength':80}))
    VC_CHOICES = (
        ('N', 'Normal'),
        ('V', 'Para la venta')
    )
    MN_CHOICES = (
        ('costomn', 'Al costo'),
        ('ventamn', 'De venta'),
        ('ventaext','Entidad Externa'),
        ('noexistmn', 'No existe')
    )
    CUC_CHOICES = (
        ('costocuc', 'Al costo'),
        ('ventacuc', 'De venta'),
        ('noexistcuc', 'No existe')
    )
    para_la_venta=forms.ChoiceField(label='Comportamiento',initial='N',required = False,widget=forms.RadioSelect,choices=VC_CHOICES)
    venta_costo_mn=forms.ChoiceField(label='Precios CUP',initial='noexistmn',required = False,widget=forms.RadioSelect,choices=MN_CHOICES)
    otro_precio_casco = forms.BooleanField(required=False,widget=forms.CheckboxInput(attrs={'disabled':'disabled'}))
    venta_costo_cuc=forms.ChoiceField(label='Precios MLC',initial='noexistcuc',required = False,widget=forms.RadioSelect,choices=CUC_CHOICES)
    
    #venta = forms.BooleanField(required=False)
    #costo = forms.BooleanField(required=False)
    
class FRepresentante(forms.Form):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    cargo = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    nombramiento = forms.CharField(label='Resol. Nombramiento',required = False,widget=forms.TextInput(attrs={'maxlength':10, 'style':'width: 78%;'}) )
    ci = forms.CharField(required = False,widget=forms.TextInput(attrs={'class':'digits', 'maxlength':11, 'minlength':11}) )

class FTransportador(forms.Form):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':35}) )
    #licencia = forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':10}) )
    ci = forms.CharField(widget=forms.TextInput(attrs={'class':'required digits', 'maxlength':11, 'minlength':11}) )
    activo = forms.BooleanField(required=True)

class Eliminar_Casco(forms.Form):
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
#    cnro=forms.IntegerField(label='Nro. del casco',widget=forms.TextInput(attrs={'class':'digits required'}) )

class FPlan(forms.Form):
    CHOICE = [('2013','2013'),('2014','2014'),('2015','2015'),('2016','2016'),('2017','2017'),
              ('2018','2018'),('2019','2019'),('2020','2020'),('2021','2021'),('2022','2022'),
              ('2023','2023'),('2024','2024'),('2025','2025'),('2026','2026'),('2027','2027'),
              ('2028','2028'),('2029','2029'),('2030','2030'),('2031','2031'),('2032','2032'),
              ('2033','2033'),('2034','2034'),('2035','2035'),('2036','2036'),('2037','2037'),
              ('2038','2038'),('2039','2039'),('2040','2040'),('2041','2041'),('2042','2042'),
              ('2043','2043'),('2044','2044'),('2045','2045'),('2046','2046'),('2047','2047'),
              ('2048','2048'),('2049','2049'),('2050','2050'),('2051','2051'),('2052','2052'),
              ('2053','2053'),('2054','2054'),('2055','2055'),('2056','2056'),('2057','2057'),
              ('2058','2058'),('2059','2059'),('2060','2060'),('2061','2061'),('2062','2062'),
              ('2063','2063'),('2064','2064'),('2065','2065'),('2066','2066'),('2067','2067'),
              ('2068','2068'),('2069','2069'),('2070','2070'),('2071','2071'),('2072','2072')]
#    ano = forms.IntegerField(label='Año',widget=forms.TextInput(attrs={'class':'required digits','min':0}))
    anoplan=forms.ChoiceField(label='Año',initial='1',widget=forms.Select(attrs={'class': 'required'}),choices=CHOICE)
    plan_contratado = forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits','min':0, 'onChange':'valida_totales();'}))
    plan_enero = forms.IntegerField(label='Enero',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_febrero = forms.IntegerField(label='Febrero',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_marzo = forms.IntegerField(label='Marzo',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_abril = forms.IntegerField(label='Abril',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_mayo = forms.IntegerField(label='Mayo',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_junio = forms.IntegerField(label='Junio',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_julio = forms.IntegerField(label='Julio',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_agosto = forms.IntegerField(label='Agosto',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_septiembre = forms.IntegerField(label='Septiembre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_octubre = forms.IntegerField(label='Octubre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_noviembre = forms.IntegerField(label='Noviembre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_diciembre = forms.IntegerField(label='Diciembre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))


class FPlanEdit(forms.Form):
#    anoplan=forms.IntegerField(widget=forms.TextInput(attrs={'class': 'required','disabled':'disabled'}))
    anoplan=forms.CharField(label='Año',widget=forms.TextInput(attrs={'class':'required', 'maxlength':4,'readonly':True}))
    plan_contratado = forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits','min':0, 'onChange':'valida_totales();'}))
    plan_enero = forms.IntegerField(label='Enero',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_febrero = forms.IntegerField(label='Febrero',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_marzo = forms.IntegerField(label='Marzo',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_abril = forms.IntegerField(label='Abril',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_mayo = forms.IntegerField(label='Mayo',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_junio = forms.IntegerField(label='Junio',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_julio = forms.IntegerField(label='Julio',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_agosto = forms.IntegerField(label='Agosto',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_septiembre = forms.IntegerField(label='Septiembre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_octubre = forms.IntegerField(label='Octubre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_noviembre = forms.IntegerField(label='Noviembre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))
    plan_diciembre = forms.IntegerField(label='Diciembre',widget=forms.TextInput(attrs={'class':'required digits','min':0,'value':0, 'onChange':'valida_totales();'}))

class VerFecha(forms.Form):
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'readonly':True}))

class Config_SMTP(forms.Form):
    servidor= forms.CharField(label='Nombre del Servidor',widget=forms.TextInput(attrs={'class':'required', 'maxlength':250}))
    puerto= forms.IntegerField(label='Puerto',widget=forms.TextInput(attrs={'class':'required digits','min':1}))
    ssl= forms.BooleanField(label='SSL/TLS',required=False)
    email = forms.EmailField(required=False,widget=forms.TextInput(attrs={'class':'email'}))
    password = forms.CharField(label='Contraseña',widget=forms.TextInput(attrs={'class':'required', 'maxlength':128}))
    
class Ocioso_Casco(forms.Form):
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
#    cnro=forms.IntegerField(label='Nro. del casco',widget=forms.TextInput(attrs={'class':'digits required'}) )

class FServicio(forms.Form):
    codigo = forms.CharField(label='Código', widget=forms.TextInput(attrs={'class': 'required', 'maxlength': 18}))
    servicio = forms.CharField(label='Asist.Técn.', widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}))
    precio_mn = forms.DecimalField(label='Precio CUP', widget=forms.TextInput(attrs={'class':'required number', 'max_digits':7, 'decimal_places':2}))
    unidad_medida = forms.ModelChoiceField(Umedida.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    activo = forms.BooleanField(initial=True, required=False)

class FProducciones(forms.Form):
    codigo = forms.CharField(label='Código', widget=forms.TextInput(attrs={'class': 'required', 'maxlength': 18}))
    producciones = forms.CharField(label='Prod.Altern.', widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}))
    precio_mn = forms.DecimalField(label='Precio CUP', widget=forms.TextInput(attrs={'class':'required number', 'max_digits':7, 'decimal_places':2}))
    precio_mn_part = forms.DecimalField(label='Precio Particular', widget=forms.TextInput(attrs={'class':'required number', 'max_digits':7, 'decimal_places':2}))
    unidad_medida = forms.ModelChoiceField(Umedida.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    activo = forms.BooleanField(initial=True, required=False)


