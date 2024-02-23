#-*- coding: utf-8 -*-
from django import forms
from comerciax.admincomerciax.models import *
from comerciax.casco.models import *
from django.forms import ModelForm, Textarea
from comerciax.utils import fecha_hoy
'''
Forms Recepcion Cliente
'''
#from django.forms.widgets import Widget, CheckboxInput



#RECEPCION DE CASCOS 
class RecepcionClienteForm(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('V', 'Para la Venta'),
        ('K', 'Vulca'),
        ('R', 'Regrabable'),
        ('O','Otro')
    )

    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='c').fechaminima(), 'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    #ajuste=forms.BooleanField(required=False)
    recepcioncliente_tipo=forms.ChoiceField(label='Tipo',initial='O',widget=forms.RadioSelect,choices=TIPO_CHOICES)
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))   


class DetalleRCForm(forms.Form):
    #idrc=forms.CharField(widget=forms.HiddenInput(),label='')
    
    medida= forms.ModelChoiceField(Producto.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    cantidad=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    nro=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    nro_final=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}))


class DetalleRCFormEdit(forms.Form):
    #idrc=forms.CharField(widget=forms.HiddenInput(),label='')
    
    medida= forms.ModelChoiceField(Producto.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    #cantidad=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    nro=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    #nro_final=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}))
    
#RECEPCION DE CASCO A PARTICULARES
class RecepcionParticularesForm(forms.Form):
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('K', 'Vulca'),
        ('R', 'Regrabable'),
        ('O','Otro')
    )

    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date','value':Fechacierre.objects.get(almacen='c').fechaminima(), 'readonly':True}))
    nombre= forms.CharField(label='Nombre y Apellidos',max_length=50,widget=forms.TextInput(attrs={'class':'required'}))
    ci= forms.CharField(label='Carné de Identidad',widget=forms.TextInput(attrs={'class':'digits required', 'maxlength':11, 'minlength':11}))
    #ajuste=forms.BooleanField(required=False)
    recepcion_tipo=forms.ChoiceField(label='Tipo',initial='O',widget=forms.RadioSelect,choices=TIPO_CHOICES)
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))   

class DetalleRPForm(forms.Form):
    #idrc=forms.CharField(widget=forms.HiddenInput(),label='')
    
    medida= forms.ModelChoiceField(Producto.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    cantidad=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    nro=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    nro_final=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}))


class DetalleRPFormEdit(forms.Form):
    #idrc=forms.CharField(widget=forms.HiddenInput(),label='')
    
    medida= forms.ModelChoiceField(Producto.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    #cantidad=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    nro=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    #nro_final=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}))    

#RECEPCION DE CASCOS A ENTIDADES EXTERNAS
class RecepcionClienteExtForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required '}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class DetalleRCExtForm(forms.Form):
    medida= forms.ModelChoiceField(Producto.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    nro=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}))
    nro_externo=forms.CharField(required=False,max_length=10,widget=forms.TextInput())


#ENTREGA DE CASCO RECHAZADOS
class CascoDCCForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))    

#ENTREGA DE CASCO RECHAZADOS
class CascoCRForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    organismo= forms.ModelChoiceField(required=False, queryset=Organismo.objects.filter().order_by('siglas_organismo'))
    provincia= forms.ModelChoiceField(required=False, queryset=Provincias.objects.filter().order_by('descripcion_provincia'))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))    

#ENTREGA DE CASCO A PRODUCCION
class CascoCCForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
 
class CascoDIPForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='p').fechaminima(),'readonly':True}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
   
class DetalleDIPForm(forms.Form):
    nro = forms.CharField(widget=forms.TextInput(attrs={'readonly':True}))
    area= forms.ModelChoiceField(Area.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    causa= forms.ModelChoiceField(CausasRechazo.objects.all(),widget=forms.Select(attrs={'class': 'required','label':'Causa de rechazo'}))
    
class TransferenciaForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    destino= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=True),widget=forms.Select(attrs={'class': 'required'}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
    
class DetalleTCForm(forms.Form):
    #idrc=forms.CharField(widget=forms.HiddenInput(),label='')
    
    medida= forms.ModelChoiceField(Producto.objects.all(),widget=forms.Select(attrs={'class': 'required'}))
    nro=forms.CharField(max_length=10,widget=forms.TextInput(attrs={'class':'required','unique':True})) 
    
class CascoERForm(forms.Form):
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))    
    
class DetalleERForm(forms.Form):
    nro = forms.CharField(widget=forms.TextInput(attrs={'readonly':True}))
    causa= forms.ModelChoiceField(CausasRechazo.objects.all(),required=False)
    
class PTExternosForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='pt').fechaminima(),'readonly':True}))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    nrofactura=forms.CharField(label='Nro. Factura',required=False,max_length=10,widget=forms.TextInput())
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))

class ReExternosForm(forms.Form):
#    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'class':'required'}))
    nro=forms.IntegerField(widget=forms.TextInput(attrs={'class':'required digits'}) )
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    nrofactura=forms.CharField(label='Nro. Factura',required=False,max_length=10,widget=forms.TextInput())
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
class CaExternosForm(forms.Form):
    nro = forms.CharField(widget=forms.TextInput(attrs={'class':'required'}))
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='c').fechaminima(),'readonly':True}))
    cliente= forms.ModelChoiceField(Cliente.objects.filter(eliminado=False,externo=True).order_by('nombre'),widget=forms.Select(attrs={'class': 'required'}))
    nrofactura=forms.CharField(label='Nro. Factura',required=False,max_length=10,widget=forms.TextInput())
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))
    
class DetallePTEForm(forms.Form):
    nro = forms.CharField(required=False,widget=forms.TextInput(attrs={'readonly':True}))
    nro_externo=forms.CharField(required=False,max_length=10,widget=forms.TextInput())
    medida_salida= forms.ModelChoiceField(Producto.objects.all(),required=False,widget=forms.Select())
    
class DetalleRREForm(forms.Form):
    nro = forms.CharField(max_length=10,widget=forms.TextInput(attrs={'readonly':True}))
    nro_externo=forms.CharField(required=False,max_length=10,widget=forms.TextInput())
    causa= forms.ModelChoiceField(CausasRechazo.objects.all(),required=False)
    
class DetalleRCEForm(forms.Form):
    nro = forms.CharField(max_length=4,widget=forms.TextInput(attrs={'readonly':True}))
    nro_externo=forms.CharField(required=False,max_length=10,widget=forms.TextInput())
    
class CascoDCForm(forms.Form):
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='pt').fechaminima(),'readonly':True}))
    dias=forms.IntegerField(label='Mín. de días en PT ', widget=forms.TextInput(attrs={'class':'required digits'}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))    

class CascoDCFormEdit(forms.Form):
    fecha=forms.DateField(required = True, widget=forms.DateInput(attrs={'class':'validate date', 'value':Fechacierre.objects.get(almacen='pt').fechaminima(),'readonly':True}))
    dias=forms.IntegerField(label='Mín. de días en PT', widget=forms.TextInput(attrs={'class':'required digits','readonly':True}) )
    observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'cols': 80, 'rows': 20,'value':''}))    

