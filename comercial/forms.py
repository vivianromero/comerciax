#-*- coding: utf-8 -*-
from django import forms
from comerciax.admincomerciax.models import *
from comerciax.casco.models import *
from django.core.validators import MinValueValidator
from django.forms import ModelForm, Textarea
from comerciax.utils import fecha_hoy
from django.contrib.admin.widgets import FilteredSelectMultiple

#############################################################
#                              REPORTES                     #
#############################################################
from admincomerciax.models import ProdAlter, Umedida


class FCerrarmes(forms.Form):
    year=forms.CharField(label='Año',max_length=4,widget=forms.TextInput(attrs={'readonly':True}))
    mes=forms.CharField(max_length=15,widget=forms.TextInput(attrs={'readonly':True}))
    
    
class FindexBalanceCasco(forms.Form):
    MES_CHOICES = (
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3','Marzo'),
        ('4','Abril'),
        ('5','Mayo'),
        ('6','Junio'),
        ('7','Julio'),
        ('8','Agosto'),
        ('9','Septiembre'),
        ('10','Octubre'),
        ('11','Noviembre'),
        ('12','Diciembre')
    )
    year=forms.CharField(label='Año',widget=forms.TextInput(attrs={'class': 'required digits','maxlength':4}))
    mes=forms.ChoiceField(initial='1',widget=forms.Select,choices=MES_CHOICES)

class Fformconsi(forms.Form):
    MES_CHOICES = (
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3','Marzo'),
        ('4','Abril'),
        ('5','Mayo'),
        ('6','Junio'),
        ('7','Julio'),
        ('8','Agosto'),
        ('9','Septiembre'),
        ('10','Octubre'),
        ('11','Noviembre'),
        ('12','Diciembre')
    )
    year=forms.CharField(label='Año',widget=forms.TextInput(attrs={'class': 'required digits','maxlength':4}))
    mes=forms.ChoiceField(initial='1',widget=forms.Select,choices=MES_CHOICES)    


class Fformorgfarmin(forms.Form):
    MES_CHOICES = (
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3','Marzo'),
        ('4','Abril'),
        ('5','Mayo'),
        ('6','Junio'),
        ('7','Julio'),
        ('8','Agosto'),
        ('9','Septiembre'),
        ('10','Octubre'),
        ('11','Noviembre'),
        ('12','Diciembre')
    )
    year=forms.CharField(label='Año',widget=forms.TextInput(attrs={'class': 'required digits','maxlength':4}))
    mes=forms.ChoiceField(initial='1',widget=forms.Select,choices=MES_CHOICES)    
    organismo = forms.ModelMultipleChoiceField(required = False,queryset=Organismo.objects.all(), widget=FilteredSelectMultiple("Organismos", is_stacked=False,attrs={'rows':'10'}))

class Fformconcixcliente(forms.Form):
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    hasta=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    
class Fformconcixorgprov(forms.Form):
    organismo=forms.ModelChoiceField(Organismo.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date required', 'value':fecha_hoy()}))
    hasta=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date required', 'value':fecha_hoy()}))

class FRpt1(forms.Form):
    organismo=forms.ModelChoiceField(Organismo.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy()}))
    hasta=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy()}))

class OfertaForm(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra')
    )
    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.ChoiceField(label='Tipo',initial='O',widget=forms.RadioSelect,choices=TIPO_CHOICES)
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
class OfertaForm1(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra')
    )
    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class OfertaForm2(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra')
    )
    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    cliente=forms.CharField(max_length=150,widget=forms.TextInput(attrs={'readonly':True}))
    tipo=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class FacturaPartForm(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra'),
        ('K','Vulca'),
        ('R','Regrabable')
    )

#    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True,'class': 'required'}))
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
    ci=forms.CharField(label='Carné de Identidad',widget=forms.TextInput(attrs={'class':'digits required', 'maxlength':11, 'minlength':11}))
#    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    nombre=forms.ModelChoiceField(label='Nombre',queryset=RecepcionParticular.objects.all().distinct('nombre').order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.ChoiceField(label='Tipo',initial='O',widget=forms.RadioSelect,choices=TIPO_CHOICES)
    recargo = forms.DecimalField(label='% Recargo', widget=forms.TextInput(
        attrs={'class': 'required number', 'max_digits': 7, 'decimal_places': 2, 'value':0.0}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    def __init__(self,*args, **kwargs):
        super(FacturaPartForm, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            self.fields["nombre"] = forms.ModelChoiceField(queryset=RecepcionParticular.objects.filter(ci=args[0]['ci']).distinct('nombre').order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
        
        if len(kwargs)>0 and kwargs['initial'].has_key('ci'):
            cii = kwargs['initial']['ci']
            self.fields["nombre"] = forms.ModelChoiceField(queryset=RecepcionParticular.objects.filter(ci=cii).distinct('nombre').order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
            
class FacturaPartForm1(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra'),
        ('K','Vulca'),
        ('R', 'Regrabable')
    )

#    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True,'class': 'required'}))
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
    ci=forms.CharField(label='Carné de Identidad',widget=forms.TextInput(attrs={'class':'digits required', 'maxlength':11, 'minlength':11,'readonly':True}))
#    cliente1=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
#    nombre=forms.ModelChoiceField(label='Nombre',queryset=RecepcionParticular.objects.all().order_by('nombre'),required=True,widget=forms.Select())
    nombre=forms.CharField(label='Nombre',widget=forms.TextInput(attrs={'class':'required', 'maxlength':50,'readonly':True}))
#     cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    recargo = forms.DecimalField(label='% Recargo', widget=forms.TextInput(
        attrs={'class': 'required number', 'max_digits': 7, 'decimal_places': 2, 'value': 0.0, 'readonly':True}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
class FacturaForm(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra'),
        ('K','Vulca'),
        ('R', 'Regrabable')
    )
#    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True,'class': 'required'}))
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
#    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente1=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.filter(externo=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
#    cliente1= forms.ModelChoiceField(Cliente.objects.filter(externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.ChoiceField(label='Tipo',initial='O',widget=forms.RadioSelect,choices=TIPO_CHOICES)
    chapa= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    licencia= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(label='Recibe',queryset=Transpotador.objects.all(),widget=forms.Select(attrs={'class': 'required','disabled':'disabled'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    def __init__(self,*args, **kwargs):
        super(FacturaForm, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = args[0]['cliente1'])),widget=forms.Select(attrs={'class': 'required'}))
        
        if len(kwargs)>0 and kwargs['initial'].has_key('cliente1'):
            cliente = kwargs['initial']['cliente1']
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = cliente.id)),widget=forms.Select(attrs={'class': 'required'}))

class FacturaForm2(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra'),
        ('K','Vulca'),
        ('R', 'Regrabable')
    )
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
    cliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.filter(externo=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    chapa= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    licencia= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(queryset=Transpotador.objects.all(),widget=forms.Select(attrs={'class': 'required','disabled':'disabled'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    def __init__(self,*args, **kwargs):
        super(FacturaForm2, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = args[0]['cliente'])),widget=forms.Select(attrs={'class': 'required'}))
        
        if len(kwargs)>0 and kwargs['initial'].has_key('cliente'):
            cliente1 = kwargs['initial']['cliente']
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = cliente1.id)),widget=forms.Select(attrs={'class': 'required'}))
            self.fields["cliente"] = forms.ModelChoiceField(queryset=Cliente.objects.select_related().filter(pk=cliente1.id),widget=forms.Select(attrs={'class': 'required'}))

class FacturaExtForm(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra')
    )
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente1=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.filter(externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.ChoiceField(label='Tipo',initial='O',widget=forms.RadioSelect,choices=TIPO_CHOICES)
    chapa= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    licencia= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(label='Recibe',queryset=Transpotador.objects.all(),widget=forms.Select(attrs={'class': 'required','disabled':'disabled'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    def __init__(self,*args, **kwargs):
        super(FacturaExtForm, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = args[0]['cliente1'])),widget=forms.Select(attrs={'class': 'required'}))
        
        if len(kwargs)>0 and kwargs['initial'].has_key('cliente1'):
            cliente = kwargs['initial']['cliente1']
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = cliente.id)),widget=forms.Select(attrs={'class': 'required'}))

class FacturaExtForm1(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra')
    )
#    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True,'class': 'required'}))
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))

#    cliente1=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    cliente1=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.filter(externo=True).order_by('nombre'),required=True,widget=forms.Select())
#     cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    chapa= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    licencia= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(queryset=Transpotador.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    def __init__(self,*args, **kwargs):
        super(FacturaExtForm1, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = args[0]['cliente1'])),widget=forms.Select(attrs={'class': 'required'}))
        
        if len(kwargs)>0 and kwargs['initial'].has_key('cliente1'):
            cliente = kwargs['initial']['cliente1']
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = cliente.id)),widget=forms.Select(attrs={'class': 'required'}))
  
class FacturaExtForm2(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('O','Otra')
    )
#    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='cm').fechaminima(), 'readonly':True}))
    cliente1=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.filter(externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    chapa= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    licencia= forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(queryset=Transpotador.objects.all(),widget=forms.Select(attrs={'class': 'required','disabled':'disabled'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    def __init__(self,*args, **kwargs):
        super(FacturaExtForm2, self).__init__(*args, **kwargs)
        
        if len(args)>0:
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = args[0]['cliente1'])),widget=forms.Select(attrs={'class': 'required'}))
        
        if len(kwargs)>0 and kwargs['initial'].has_key('cliente1'):
            cliente2 = kwargs['initial']['cliente1']
            self.fields["transportador"] = forms.ModelChoiceField(queryset=Transpotador.objects.select_related().filter(activo=True,contrato__cerrado=False,contrato__clientecontrato__cliente=Cliente.objects.get(id = cliente2.id)),widget=forms.Select(attrs={'class': 'required'}))
            self.fields["cliente1"] = forms.ModelChoiceField(queryset=Cliente.objects.select_related().filter(pk=cliente2.id),widget=forms.Select(attrs={'class': 'required'}))

  
class PagoEfectForm(forms.Form):
    nombre=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}))
    ci=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':11}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    moneda=forms.ModelChoiceField(Monedas.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    #pago_en_efectivo=forms.BooleanField(required=False)
    importe=forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class PagoEfectForm1(forms.Form):
    nombre=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}))
    ci=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':11}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente=forms.CharField(max_length=150,widget=forms.TextInput(attrs={'readonly':True}))
    moneda=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    #pago_en_efectivo=forms.BooleanField(required=False)
    importe=forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))


class PagoEfectPartForm(forms.Form):
    nombre=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}))
    ci=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':11}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    moneda=forms.ModelChoiceField(Monedas.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    #pago_en_efectivo=forms.BooleanField(required=False)
    importe=forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class PagoEfectPartForm1(forms.Form):
    nombre=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':50}))
    ci=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':11}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    moneda=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    #pago_en_efectivo=forms.BooleanField(required=False)
    importe=forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

                      
class PagosForm(forms.Form):
    nro=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':10}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    
    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    moneda=forms.ModelChoiceField(Monedas.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    tipo=forms.ModelChoiceField(FormasPago.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    importe=forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class PagosForm1(forms.Form):
    nro=forms.CharField(widget=forms.TextInput(attrs={'class':'required', 'maxlength':10}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
#    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
#    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    
#    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    cliente=forms.CharField(max_length=150,widget=forms.TextInput(attrs={'readonly':True}))
    moneda=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    tipo=forms.ModelChoiceField(FormasPago.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    importe=forms.DecimalField(widget=forms.TextInput(attrs={'class':'required number','max_digits':7, 'decimal_places':2}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class Rep_RegContratos(forms.Form):
    ORD_CHOICES = (
        ('cliente', 'Cliente'),
        ('nro', 'Número de Contrato'),
    )
    TIPO_CHOICES = (
        ('G','---------'),          
        ('N', 'Normal'),
        ('V', 'Para la Venta'),
    )
    PREC_CHOICES = (
        ('G','---------'),          
        ('N', 'No Existe'),
        ('V', 'De Venta'),
        ('C', 'De Costo'),
    )
    CERR_CHOICES = (
        ('G','---------'),          
        ('S', 'Si'),
        ('N', 'No'),
    )
    orden=forms.ChoiceField(label='Ordenar por',initial='cliente',required = False,widget=forms.RadioSelect,choices=ORD_CHOICES)
    cliente=forms.ModelChoiceField(Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    nro=forms.CharField(label='Nro. Contrato', required=False, widget=forms.TextInput())
    tipo=forms.ChoiceField(label='Tipo de Contrato',required = False,widget=forms.Select(),choices=TIPO_CHOICES)
    cerrado=forms.ChoiceField(required = False,widget=forms.Select(),choices=CERR_CHOICES)
    preciocup=forms.ChoiceField(label='Precio CUP',required = False,widget=forms.Select(),choices=PREC_CHOICES)
    preciocuc=forms.ChoiceField(label='Precio MLC',required = False,widget=forms.Select(),choices=PREC_CHOICES)
    dias=forms.IntegerField(label='Máx. de días para caducar',required = False,widget=forms.TextInput(attrs={'class':'digits'}) )

class Rep_ContratosFechaVenc(forms.Form):
    MES_CHOICES = (
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3','Marzo'),
        ('4','Abril'),
        ('5','Mayo'),
        ('6','Junio'),
        ('7','Julio'),
        ('8','Agosto'),
        ('9','Septiembre'),
        ('10','Octubre'),
        ('11','Noviembre'),
        ('12','Diciembre')
    )
    ORD_CHOICES = (
        ('cliente', 'Cliente'),
        ('fecha', 'Fecha de Vencimiento'),
    )
    orden=forms.ChoiceField(label='Ordenar por',initial='cliente',required = False,widget=forms.RadioSelect,choices=ORD_CHOICES)
    year=forms.CharField(label='Año',widget=forms.TextInput(attrs={'class': 'required digits','maxlength':4}))
    mes=forms.ChoiceField(initial='1',required=True,widget=forms.Select,choices=MES_CHOICES)

    
class Rep_CascosCliente(forms.Form):
    ORD_CHOICES = (
        ('cliente', 'Cliente'),
        ('nro', 'Número de Casco'),
    )
    
    ESTADO_CHOICES = (
               ('G','---------'), 
               ('Casco','Almacén de Casco'),
               ('Produccion','Proceso de Producción'),
               ('PT','Almacén Producción Terminada'),
               ('Transferencia','Transferencia'),
               ('DIP','Devuelto a Inservible'),
               ('DVP','Devuelto a Vulca'),
               ('ER','Rechazado por error revisión'),
               ('ECR','Casco Rechazado Entregado'),
               ('REE','Rechazado por Entidad Externa'),
               ('DCC','Devuelto al Cliente'),
               ('DC','Casco Decomisado'),
               ('Factura','Facturado'),
    )
    particular = forms.BooleanField(required=False)
    ocioso = forms.BooleanField(required=False)
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    cnro=forms.IntegerField(label='Nro. del casco',required=False,widget=forms.TextInput(attrs={'class':'digits'}) )
    estado=forms.ChoiceField(label='Estado',required = False,widget=forms.Select(),choices=ESTADO_CHOICES)
    cfecha=forms.DateField(label='Entrada desde',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    cfechahasta=forms.DateField(label='Entrada hasta',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    orden=forms.ChoiceField(label='Ordenar por',initial='cliente',required = False,widget=forms.RadioSelect,choices=ORD_CHOICES)
    
class Rep_CascosTraza(forms.Form):
    particular = forms.BooleanField(required=False)
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    cnro=forms.IntegerField(label='Nro. del casco',required=False,widget=forms.TextInput(attrs={'class':'digits'}) )
    cfecha=forms.DateField(label='Traza desde',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))

class Rep_CascosVenta(forms.Form):
    ORD_CHOICES = (
        ('medida', 'Medida'),
        ('cliente', 'Cliente'),
    )
    orden=forms.ChoiceField(label='Ordenar por',initial='medida',required = False,widget=forms.RadioSelect,choices=ORD_CHOICES)

class Rep_CascosEstado(forms.Form):
    ORD_CHOICES = (
        ('medida', 'Medida'),
        ('cliente', 'Cliente'),
    )

    ESTADO_CHOICES = (
               ('G','---------'), 
               ('Casco','Almacén de Casco'),
               ('Produccion','Proceso de Producción'),
               ('PT','Almacén Producción Terminada'),
               ('Transferencia','Transferencia'),
               ('DIP','Devuelto a Inservible'),
               ('DVP','Devuelto a Vulca'),
               ('ER','Rechazado por error revisión'),
               ('ECR','Casco Rechazado Entregado'),
               ('REE','Rechazado por Entidad Externa'),
               ('DCC','Devuelto al Cliente'),
               ('DC','Casco Decomisado'),
               ('Factura','Facturado'),
    )
    particular = forms.BooleanField(required=False)
    ocioso = forms.BooleanField(required=False)
    venta = forms.BooleanField(required=False)
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    medida= forms.ModelChoiceField(label='Medida',queryset=Producto.objects.all().order_by('descripcion'),required=False,widget=forms.Select())
    dias=forms.IntegerField(label='Mín. de días',required=False,widget=forms.TextInput(attrs={'class':'digits'}) )
    diasmax=forms.IntegerField(label='Max. de días',required=False,widget=forms.TextInput(attrs={'class':'digits'}) )
    estado=forms.ChoiceField(label='Estado',required = False,widget=forms.Select(),choices=ESTADO_CHOICES)
    orden=forms.ChoiceField(label='Ordenar por',initial='medida',required = False,widget=forms.RadioSelect,choices=ORD_CHOICES)
    
class Rep_FacturaCliente(forms.Form):
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    fecha_desde=forms.DateField(label='Emitida desde',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha_hasta=forms.DateField(label='Emitida hasta',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))

class Rep_RegFacturas(forms.Form):
    fecha_desde=forms.DateField(label='Emitida desde',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    fecha_hasta=forms.DateField(label='Emitida hasta',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))    
    
class Rep_FacturaCobrar(forms.Form):
    ORD_CHOICES = (
        ('cliente', 'Cliente'),
        ('edad', 'Edad de la Factura'),
    )
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    edad=forms.IntegerField(label='Edad mínima',required = False,widget=forms.TextInput(attrs={'class':'digits'}) )
    orden=forms.ChoiceField(label='Ordenar por',initial='cliente',required = False,widget=forms.RadioSelect,choices=ORD_CHOICES)

class Rep_RegCobros(forms.Form):
    SEL_CHOICES = (
        ('Si', 'Si'),
        ('No', 'No'),
    )
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    cfecha=forms.DateField(label='Cobros desde',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    cmoneda=forms.ModelChoiceField(label='Moneda',queryset=Monedas.objects.all(),required=False,widget=forms.Select())
    seleccion=forms.ChoiceField(label='Desglosado por Facturas',initial='Si',required = False,widget=forms.RadioSelect,choices=SEL_CHOICES)

class Rep_VentasDecomiso(forms.Form):
    
    organismo= forms.ModelChoiceField(label='Organismo',required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),widget=forms.Select())
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',queryset=Cliente.objects.all().order_by('nombre'),required=False,widget=forms.Select())
    cfecha=forms.DateField(label='Desde',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    dfecha=forms.DateField(label='Hasta',required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    desglosado = forms.BooleanField(required=False,widget=forms.CheckboxInput(attrs={'checked':'checked'}))
    
class DetalleFacturaForm(forms.Form):
    medida_salida= forms.ModelChoiceField(Producto.objects.all(),required=False,widget=forms.Select())
    
class TransfEnviadas(forms.Form):
    clientetransf=forms.ModelChoiceField(label='Transferido a',queryset=Cliente.objects.filter(externo=True).order_by('nombre'),required=False,widget=forms.Select())
    medida= forms.ModelChoiceField(label='Medida',queryset=Producto.objects.all().order_by('descripcion'),required=False,widget=forms.Select())
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date required', 'value':fecha_hoy()}))
    hasta=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date required', 'value':fecha_hoy()}))  

class MovCascos(forms.Form):
    MOVIM_CHOICES = ( 
               ('Casco','Recepción de Cascos'),
               ('Produccion','Entrada a Producción'),
               ('PT','Entrada a Producción Terminada'),
               ('Decomiso','Decomisados'),
               ('Factura','Facturados'),
    )
    SEL_CHOICES = (
        ('Si', 'Si'),
        ('No', 'No'),
    )
    movimiento=forms.ChoiceField(label='Movimiento',choices=MOVIM_CHOICES,widget=forms.Select(attrs={'class':'required'}))
    organismo=forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',required=False, queryset=Cliente.objects.filter().order_by('nombre'))
    medida= forms.ModelChoiceField(label='Medida',queryset=Producto.objects.all().order_by('descripcion'),required=False,widget=forms.Select())
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    hasta=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    seleccionar_por=forms.ChoiceField(label='Desglosado por Medida',initial='Si',required = False,widget=forms.RadioSelect,choices=SEL_CHOICES)
    agrupado_por=forms.BooleanField(label='Agrupar por Medida',required=False)

class RepPlanes(forms.Form):
    SEL_CHOICES = (
        ('Si', 'Si'),
        ('No', 'No'),
    )
    organismo=forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',required=False, queryset=Cliente.objects.filter().order_by('nombre'))
    ano=forms.IntegerField(label='Año',required = True,widget=forms.TextInput(attrs={'class':'digits required'}) )
    seleccion=forms.ChoiceField(label='Contratados',initial='Si',required = False,widget=forms.RadioSelect,choices=SEL_CHOICES)

class RepPTCantidad(forms.Form):
    SEL_CHOICES = (
        ('Si', 'Si'),
        ('No', 'No'),
    )
    organismo=forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',required=False, queryset=Cliente.objects.filter().order_by('nombre'))
    medida= forms.ModelChoiceField(label='Medida',queryset=Producto.objects.all().order_by('descripcion'),required=False,widget=forms.Select())
    cantidad=forms.IntegerField(label='Más de',required = True,widget=forms.TextInput(attrs={'class':'digits required'}) )
    seleccion=forms.ChoiceField(label='Desglosado por medida',initial='Si',required = False,widget=forms.RadioSelect,choices=SEL_CHOICES)

class Fconciliacion(forms.Form):
    organismo=forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',required=False, queryset=Cliente.objects.filter().order_by('nombre'))
    
class FServicios(forms.Form):
    organismo=forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',required=False, queryset=Cliente.objects.filter().order_by('nombre'))
    desde=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    hasta=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':fecha_hoy(),'readonly':True}))
    
class RepCumpPlanes(forms.Form):
    organismo=forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    ccliente=forms.ModelChoiceField(label='Cliente',required=False, queryset=Cliente.objects.filter().order_by('nombre'))
    ano=forms.IntegerField(label='Año',required = True,widget=forms.TextInput(attrs={'class':'digits required'}) )


class FacturaServiciosForm(forms.Form):
    fecha = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'class': 'validate date', 'value': Fechacierre.objects.get(almacen='cm').fechaminima(),
               'readonly': True}))
    #    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    organismo = forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),
                                       widget=forms.Select())
    provincia = forms.ModelChoiceField(required=False,
                                       queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente1 = forms.ModelChoiceField(label='Cliente',
                                      queryset=Cliente.objects.filter(externo=False).order_by('nombre'),
                                      widget=forms.Select(attrs={'class': 'required'}))
    #    cliente1= forms.ModelChoiceField(Cliente.objects.filter(externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    chapa = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'required'}))
    licencia = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(label='Recibe', queryset=Transpotador.objects.all(),
                                           widget=forms.Select(attrs={'class': 'required', 'disabled': 'disabled'}))
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 20, 'value': ''}))

    def __init__(self, *args, **kwargs):
        super(FacturaServiciosForm, self).__init__(*args, **kwargs)

        if len(args) > 0:
            self.fields["transportador"] = forms.ModelChoiceField(
                queryset=Transpotador.objects.select_related().filter(activo=True, contrato__cerrado=False,
                                                                      contrato__clientecontrato__cliente=Cliente.objects.get(
                                                                          id=args[0]['cliente1'])),
                widget=forms.Select(attrs={'class': 'required'}))

        if len(kwargs) > 0 and kwargs['initial'].has_key('cliente1'):
            cliente = kwargs['initial']['cliente1']
            self.fields["transportador"] = forms.ModelChoiceField(
                queryset=Transpotador.objects.select_related().filter(activo=True, contrato__cerrado=False,
                                                                      contrato__clientecontrato__cliente=Cliente.objects.get(
                                                                          id=cliente.id)),
                widget=forms.Select(attrs={'class': 'required'}))


class FacturaServiciosForm2(forms.Form):
    fecha = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'class': 'validate date', 'value': Fechacierre.objects.get(almacen='cm').fechaminima(),
               'readonly': True}))
    cliente = forms.ModelChoiceField(label='Cliente', queryset=Cliente.objects.filter(externo=False).order_by('nombre'),
                                     widget=forms.Select(attrs={'class': 'required'}))
    chapa = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'required'}))
    licencia = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'required'}))
    transportador = forms.ModelChoiceField(queryset=Transpotador.objects.all(),
                                           widget=forms.Select(attrs={'class': 'required', 'disabled': 'disabled'}))
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 20, 'value': ''}))

    def __init__(self, *args, **kwargs):
        super(FacturaServiciosForm2, self).__init__(*args, **kwargs)

        if len(args) > 0:
            self.fields["transportador"] = forms.ModelChoiceField(
                queryset=Transpotador.objects.select_related().filter(activo=True, contrato__cerrado=False,
                                                                      contrato__clientecontrato__cliente=Cliente.objects.get(
                                                                          id=args[0]['cliente'])),
                widget=forms.Select(attrs={'class': 'required'}))

        if len(kwargs) > 0 and kwargs['initial'].has_key('cliente'):
            cliente1 = kwargs['initial']['cliente']
            self.fields["transportador"] = forms.ModelChoiceField(
                queryset=Transpotador.objects.select_related().filter(activo=True, contrato__cerrado=False,
                                                                      contrato__clientecontrato__cliente=Cliente.objects.get(
                                                                          id=cliente1.id)),
                widget=forms.Select(attrs={'class': 'required'}))
            self.fields["cliente"] = forms.ModelChoiceField(
                queryset=Cliente.objects.select_related().filter(pk=cliente1.id),
                widget=forms.Select(attrs={'class': 'required'}))

class FacturaProduccionesForm(forms.Form):
    fecha = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'class': 'validate date', 'value': Fechacierre.objects.get(almacen='cm').fechaminima(),
               'readonly': True}))
    #    cliente=forms.ModelChoiceField(Cliente.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    organismo = forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'),
                                       widget=forms.Select())
    provincia = forms.ModelChoiceField(required=False,
                                       queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente1 = forms.ModelChoiceField(label='Cliente',
                                      queryset=Cliente.objects.filter(externo=False).order_by('nombre'),
                                      widget=forms.Select(attrs={'class': 'required'}))
    #    cliente1= forms.ModelChoiceField(Cliente.objects.filter(externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    # chapa = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'required'}))
    # licencia = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'required'}))
    # transportador = forms.ModelChoiceField(label='Recibe', queryset=Transpotador.objects.all(),
    #                                        widget=forms.Select(attrs={'class': 'required', 'disabled': 'disabled'}))
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 20, 'value': ''}))

    def __init__(self, *args, **kwargs):
        super(FacturaProduccionesForm, self).__init__(*args, **kwargs)

        # if len(args) > 0:
        #     self.fields["transportador"] = forms.ModelChoiceField(
        #         queryset=Transpotador.objects.select_related().filter(activo=True, contrato__cerrado=False,
        #                                                               contrato__clientecontrato__cliente=Cliente.objects.get(
        #                                                                   id=args[0]['cliente1'])),
        #         widget=forms.Select(attrs={'class': 'required'}))

        if len(kwargs) > 0 and kwargs['initial'].has_key('cliente1'):
            cliente = kwargs['initial']['cliente1']
            # self.fields["transportador"] = forms.ModelChoiceField(
            #     queryset=Transpotador.objects.select_related().filter(activo=True, contrato__cerrado=False,
            #                                                           contrato__clientecontrato__cliente=Cliente.objects.get(
            #                                                               id=cliente.id)),
            #     widget=forms.Select(attrs={'class': 'required'}))


class FacturaProduccionesForm2(forms.Form):
    fecha = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'class': 'validate date', 'value': Fechacierre.objects.get(almacen='cm').fechaminima(),
               'readonly': True}))
    cliente = forms.ModelChoiceField(label='Cliente', queryset=Cliente.objects.filter(externo=False).order_by('nombre'),
                                     widget=forms.Select(attrs={'class': 'required'}))
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 80, 'rows': 20, 'value': ''}))

    def __init__(self, *args, **kwargs):
        super(FacturaProduccionesForm2, self).__init__(*args, **kwargs)

        if len(kwargs) > 0 and kwargs['initial'].has_key('cliente'):
            cliente1 = kwargs['initial']['cliente']
            self.fields["cliente"] = forms.ModelChoiceField(
                queryset=Cliente.objects.select_related().filter(pk=cliente1.id),
                widget=forms.Select(attrs={'class': 'required'}))


class DetalleFacturaProdAlterForm(forms.Form):
    producto = forms.ModelChoiceField(ProdAlter.objects.all(),  widget=forms.Select(attrs={"class": "required"}))
    cantidad = forms.DecimalField(
        widget=forms.TextInput(attrs={'class': 'required number'}),
        max_digits=7,
        decimal_places=2,
        initial=0.00
    )

class DetalleFacturaProdAlterForm2(forms.Form):
    producto = forms.ModelChoiceField(ProdAlter.objects.all(), required = False, widget=forms.Select(attrs={"disabled": "disabled"}))
    cantidad = forms.DecimalField(
        widget=forms.TextInput(attrs={'class': 'required number'}),
        max_digits=7,
        decimal_places=2,
        initial=0.00
    )

    # def __init__(self, *args, **kwargs):
    #     super(DetalleFacturaProdAlterForm, self).__init__(*args, **kwargs)
    #
    #     if len(kwargs) > 0 and kwargs['initial'].has_key('cantidad'):
    #         self.fields["producto"].widget.attrs= {"disabled": "disabled"}
    #         self.fields["producto"].required = False
