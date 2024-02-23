# -*- coding: utf-8 -*-
from django.db import models
from comerciax.admincomerciax.models import *
from comerciax.casco.models import Casco,Doc
from django.contrib.auth.models import User
from django.db.models import Sum
from comerciax import utils
from django.db.models import Count

'''
Ofertas a los clientes
'''

class Oferta(models.Model):
    doc_oferta=models.OneToOneField(Doc,primary_key=True, unique=True)
    oferta_nro=models.CharField(max_length=10)
    cliente=models.ForeignKey(Cliente,on_delete=models.PROTECT)
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('V', 'De Venta'),
        ('O','Otra')
    )
    oferta_tipo=models.CharField(max_length=1, choices=TIPO_CHOICES)
    def __unicode__(self):
        return self.oferta_nro
    class Meta:
        ordering = ['oferta_nro']
        permissions = (("oferta","oferta"),)
        
    
    def get_importecuc(self,*deci):
        importes=DetalleOferta.objects.filter(oferta=self.doc_oferta).aggregate(Sum('precio_cuc')) 
        if len(deci)>0:
            if importes['precio_cuc__sum'] is None:
                return 0
            return importes['precio_cuc__sum']
        a1=0.00 if importes['precio_cuc__sum'] is None else importes['precio_cuc__sum']
        return '$'+'{:20,.2f}'.format(a1)   
    
    def get_importecup(self,*deci):
        
        importes=DetalleOferta.objects.filter(oferta=self.doc_oferta).aggregate(Sum('precio_mn'))
        if len(deci)>0:
            if importes['precio_mn__sum'] is None:
                return 0
            return importes['precio_mn__sum']
        a1=0.00 if importes['precio_mn__sum'] is None else importes['precio_mn__sum']
        return '$'+'{:20,.2f}'.format(a1)
    
    
    def get_importe_venta(self,*deci):
        
        importes=DetalleOferta.objects.filter(oferta=self.doc_oferta,casco__venta=True, casco__decomisado=False).aggregate(Sum('precio_casco'))
        if len(deci)>0:
            if importes['precio_casco__sum'] is None:
                return 0
            return importes['precio_casco__sum']
        a1=0.00 if importes['precio_casco__sum'] is None else importes['precio_casco__sum']
        return '$'+'{:20,.2f}'.format(a1)
    
    def get_importetotalcup(self,*deci):
        importe_total=self.get_importecup(2)+self.get_importe_venta(2)
        if len(deci)>0:
            return importe_total
        return '$'+'{:20,.2f}'.format(importe_total)
                                                                                                                                               

class DetalleOferta(models.Model):
    id_detalleofertafactura=models.CharField(max_length=40, primary_key=True, unique=True)
    oferta = models.ForeignKey(Oferta)
    casco = models.ForeignKey(Casco)
    precio_mn=models.DecimalField(max_digits=7, decimal_places=2,default=0.0)
    precio_cuc=models.DecimalField(max_digits=7, decimal_places=2,default=0.0)
    precio_casco=models.DecimalField(max_digits=7, decimal_places=2,default=0.0)

    def format_precio_mn(self):
        return '{:20,.2f}'.format(self.precio_mn) 
        
    def format_precio_cuc(self):
        return '{:20,.2f}'.format(self.precio_cuc)
    
    def format_precio_casco(self):
        return '{:20,.2f}'.format(self.precio_casco)
        
'''
Factura a los clientes
El detalle de la factura es el de la oferta que la origino
'''
class FacturasParticular(models.Model):
    doc_factura=models.OneToOneField(Doc,primary_key=True, unique=True)
    factura_nro=models.CharField(max_length=10)
    cancelada=models.BooleanField(default=False)
    ci = models.CharField(max_length=11)
    nombre = models.CharField(max_length=50)
    tipo=models.CharField(max_length=1)
    confirmada=models.CharField(max_length=45)
    confirmar=models.BooleanField(default=0)
    recargo = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    
    def __unicode__(self):
        return self.factura_nro
    
    class Meta:
        ordering = ['factura_nro']
        permissions = (("factura","factura"),)
    
    def get_importe(self,*deci):
        
        importes=DetalleFacturaPart.objects.filter(factura=self.doc_factura).aggregate(Sum('precio_particular'))
        if len(deci)>0:
            if importes['precio_particular__sum'] is None:
                return 0
            return importes['precio_particular__sum']
        a1=0.00 if importes['precio_particular__sum'] is None else importes['precio_particular__sum']
        return '$'+'{:20,.2f}'.format(a1)

    def get_importe_total(self, *recarga):
        # recargo = float(self.recargo)
        # importes = DetalleFacturaPart.objects.filter(factura=self.doc_factura).aggregate(Sum('precio_particular'))
        #
        # a1 = 0.00 if importes['precio_particular__sum'] is None else importes['precio_particular__sum']
        # a1 = float(a1)
        # val = utils.redondeo((a1 * recargo) / 100, 2)
        # importetotalcup_ = utils.redondeo(a1 + val, 2)
        importetotalcup_ = self.get_importe_total_value(recarga)
        return '$' + '{:20,.2f}'.format(importetotalcup_)

    def get_importe_total_value(self, *recarga):
        recargo = float(self.recargo)
        importes = DetalleFacturaPart.objects.filter(factura=self.doc_factura).aggregate(Sum('precio_particular'))

        a1 = 0.00 if importes['precio_particular__sum'] is None else importes['precio_particular__sum']
        a1 = float(a1)
        val = utils.redondeo((a1 * recargo) / 100, 2)
        importetotalcup_ = utils.redondeo(a1 + val, 2)

        return importetotalcup_
    
    def get_importe_venta(self,*deci):
        
        importes=DetalleFacturaPart.objects.filter(factura=self.doc_factura,casco__venta=True, casco__decomisado=False).aggregate(Sum('precio_casco'))
        if len(deci)>0:
            if importes['precio_casco__sum'] is None:
                return 0
            return importes['precio_casco__sum']
        a1=0.00 if importes['precio_casco__sum'] is None else importes['precio_casco__sum']
        return '$'+'{:20,.2f}'.format(a1)
    
    def get_importetotalcup(self,*deci):
        importe_total=self.get_importe(2)+self.get_importe_venta(2)
        if len(deci)>0:
            return importe_total
        return '$'+'{:20,.2f}'.format(importe_total)
    
    
    def get_confirmada(self):
        import hashlib
        pkf=self.pk.__str__()
        
        if self.confirmada==hashlib.sha1(pkf+'NO').hexdigest():
            return 'N'
        elif self.confirmada==hashlib.sha1(pkf+'YES').hexdigest():
            return 'S'   
        else:
            return 'E'  
    
    def get_porpagar(self,*deci):
        importes=PagosFacturasPart.objects.select_related().filter(facturas=self.doc_factura,pagos__tipo_moneda='1').aggregate(Sum('importe_pagado'))
        pagadocup=0 if importes['importe_pagado__sum']==None else importes['importe_pagado__sum']
        importe=FacturasParticular.objects.get(pk=self).get_importe(1)
        importecup=0 if importe==None else importe
        porpagar=importecup-pagadocup
        if len(deci)>0:
            return porpagar
        return '$'+'{:20,.2f}'.format(porpagar) 
   
    def cantidad_casco(self):  
        return DetalleFacturaPart.objects.select_related().filter(factura=self.doc_factura).count()   
    
    def edad_factura(self):
        import datetime
        return (datetime.date.today()-self.doc_factura.fecha_doc).days
    
    def get_fecha(self):
        fecha=self.doc_factura.fecha_doc
        dia=fecha.day
        mes=fecha.month
        year=fecha.year
        dia1='0'+str(dia) if len(str(dia))<2 else str(dia)
        mes1='0'+str(mes) if len(str(mes))<2 else str(mes)
        return dia1+"/"+mes1+"/"+str(year)   
    
    def get_renglones(self):
        detallesFact = DetalleFacturaPart.objects.select_related().filter(factura=self.doc_factura).values('factura','precio_particular','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
                                       
        detallesFact_venta = DetalleFacturaPart.objects.select_related().filter(factura=self.doc_factura,casco__venta=True,casco__decomisado=False).values('factura','precio_casco','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
                                                                            
        return detallesFact.__len__()+detallesFact_venta.__len__() 
    
class DetalleFacturaPart(models.Model):
    id_detalle=models.CharField(max_length=40, primary_key=True, unique=True)
    factura = models.ForeignKey(FacturasParticular)
    casco = models.ForeignKey(Casco)
    precio_particular=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    precio_casco=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    
    def format_precio_particular(self):
        return '{:20,.2f}'.format(self.precio_particular)
    
    def format_precio_casco(self):
        return '{:20,.2f}'.format(self.precio_casco)

    
class Facturas(models.Model):
    doc_factura=models.OneToOneField(Doc,primary_key=True, unique=True)
    factura_nro=models.CharField(max_length=10)
    transportador=models.ForeignKey(Transpotador,on_delete=models.PROTECT)
    cancelada=models.BooleanField(default=False)
    chapa=models.CharField(max_length=10)
    licencia=models.CharField(max_length=10)
    cliente=models.ForeignKey(Cliente,on_delete=models.PROTECT)
    tipo=models.CharField(max_length=1)
    confirmada=models.CharField(max_length=45)
    confirmar=models.BooleanField(default=0)
    def __unicode__(self):
        return self.factura_nro
    
    class Meta:
        ordering = ['confirmar','factura_nro']
        permissions = (("factura","factura"),)
    
    def get_importecuc(self,*deci):
        
#        importes=DetalleFactura.objects.filter(factura=self.doc_factura).aggregate(Sum('precio_cuc'))
        importes=self.detallefactura_set.aggregate(Sum('precio_cuc'))
        if len(deci)>0:
            if importes['precio_cuc__sum'] is None:
                return 0
            return importes['precio_cuc__sum']
        a1=0.00 if importes['precio_cuc__sum'] is None else importes['precio_cuc__sum']
        return '${:20,.2f}'.format(a1)
    
    def get_importecup(self,*deci):
#        importes=DetalleFactura.objects.filter(factura=self.doc_factura).aggregate(Sum('precio_mn'))
        importes=self.detallefactura_set.aggregate(Sum('precio_mn'))
        if len(deci)>0:
            if importes['precio_mn__sum'] is None:
                return 0
            return importes['precio_mn__sum']
        a1=0.00 if importes['precio_mn__sum'] is None else importes['precio_mn__sum']
        return '${:20,.2f}'.format(a1)
    
    
    def get_importe_venta(self,*deci):
        
#        importes=DetalleFactura.objects.filter(factura=self.doc_factura,casco__venta=True, casco__decomisado=False).aggregate(Sum('precio_casco'))
        importes=self.detallefactura_set.filter(casco__venta=True, casco__decomisado=False).aggregate(Sum('precio_casco'))
        if len(deci)>0:
            if importes['precio_casco__sum'] is None:
                return 0
            return importes['precio_casco__sum']
        a1=0.00 if importes['precio_casco__sum'] is None else importes['precio_casco__sum']
        return '${:20,.2f}'.format(a1)
    
    def get_importetotalcup(self,*deci):
        importe_total=self.get_importecup(2)+self.get_importe_venta(2)
        if len(deci)>0:
            return importe_total
        return '${:20,.2f}'.format(importe_total)
    
    def get_confirmada(self):
        import hashlib
        pkf=self.pk.__str__()
        
        if self.confirmada==hashlib.sha1(pkf+'NO').hexdigest():
            return 'N'
        elif self.confirmada==hashlib.sha1(pkf+'YES').hexdigest():
            return 'S'   
        else:
            return 'E'  
    
    def get_porpagar_cup(self,*deci):
#        importes=PagosFacturas.objects.select_related().filter(facturas=self.doc_factura,pagos__tipo_moneda='1').aggregate(Sum('importe_pagado'))
        importes=self.pagosfacturas_set.filter(pagos__tipo_moneda='1').aggregate(Sum('importe_pagado'))
        pagadocup=0 if importes['importe_pagado__sum']==None else importes['importe_pagado__sum']
        importe=Facturas.objects.get(pk=self).get_importetotalcup(1)
        importecup=0 if importe==None else importe
        porpagar=importecup-pagadocup
        if len(deci)>0:
            return porpagar
        return '$'+'{:20,.2f}'.format(porpagar) 

    def get_porpagar_cuc(self,*deci):
#        importes=PagosFacturas.objects.select_related().filter(facturas=self.doc_factura,pagos__tipo_moneda='2').aggregate(Sum('importe_pagado'))
        importes=self.pagosfacturas_set.filter(pagos__tipo_moneda='2').aggregate(Sum('importe_pagado'))
        pagadocuc=0 if importes['importe_pagado__sum']==None else importes['importe_pagado__sum']
        importe=Facturas.objects.get(pk=self).get_importecuc(1)
        importecuc=0 if importe==None else importe
        porpagar=importecuc-pagadocuc
        
        if len(deci)>0:
            return porpagar
        return '$'+'{:20,.2f}'.format(porpagar)
    
    def cantidad_casco(self):  
#        return DetalleFactura.objects.select_related().filter(factura=self.doc_factura).count()
        return self.detallefactura_set.count()   
    
    def edad_factura(self):
        import datetime
        return (datetime.date.today()-self.doc_factura.fecha_doc).days
    
    def get_fecha(self):
        fecha=self.doc_factura.fecha_doc
        dia=fecha.day
        mes=fecha.month
        year=fecha.year
        dia1='0'+str(dia) if len(str(dia))<2 else str(dia)
        mes1='0'+str(mes) if len(str(mes))<2 else str(mes)
        return dia1+"/"+mes1+"/"+str(year)
    
    def get_renglones(self):
        detallesFact = DetalleFactura.objects.select_related().filter(factura=self.doc_factura).values('factura','precio_mn','precio_cuc','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
                                       
        detallesFact_venta = DetalleFactura.objects.select_related().filter(factura=self.doc_factura,casco__venta=True,casco__decomisado=False).values('factura','precio_casco','casco__producto_salida',\
                                                                            'casco__producto_salida__codigo','casco__producto_salida__descripcion',\
                                                                            'casco__producto_salida__um__descripcion')\
                                                                            .annotate(cantidad=Count('casco__producto_salida'))
                                                                            
        return detallesFact.__len__()+detallesFact_venta.__len__()
    
class DetalleFactura(models.Model):
    id_detalle=models.CharField(max_length=40, primary_key=True, unique=True)
    factura = models.ForeignKey(Facturas)
    casco = models.ForeignKey(Casco)
    precio_mn=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    precio_cuc=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    precio_casco=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    
    def format_precio_mn(self):
        return '{:20,.2f}'.format(self.precio_mn)
    
    def format_precio_cuc(self):
        return '{:20,.2f}'.format(self.precio_cuc)
    
    def format_precio_casco(self):
#        prec=0.0 if self.precio_casco==None else self.precio_casco
        return '{:20,.2f}'.format(self.precio_casco)
    
'''
Control de los pagos de los clientes
'''

class Pagos(models.Model):
    id_pago=models.CharField(max_length=40, primary_key=True, unique=True)
    fecha_pago=models.DateField()
    fecha_operacion=models.DateTimeField(auto_now=True)
    importe=models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    efectivo=models.BooleanField(default=False)
    particulares=models.BooleanField(default=False)
    tipo_moneda= models.ForeignKey(Monedas,on_delete=models.PROTECT) 
    observaciones=models.TextField()
    operador=models.ForeignKey(User,on_delete=models.PROTECT)
#    cliente=models.ForeignKey(Cliente,on_delete=models.PROTECT)
    deposito_adelantado=models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    class Meta:
        permissions = (("pagos","pagos"),)
        
    def format_importe(self):
        return '{:20,.2f}'.format(self.importe) 
    
    def get_deposito_adelantado(self):
        return '{:20,.2f}'.format(self.importe) 
    
    def format_deposito_adelantado(self):
        return '{:20,.2f}'.format(self.deposito_adelantado) 
    
    
class PagosClientes(models.Model):
    id_pagocliente=models.CharField(max_length=40, primary_key=True, unique=True)
    pagos = models.OneToOneField(Pagos,on_delete=models.CASCADE)
    cliente=models.ForeignKey(Cliente,on_delete=models.PROTECT)
 
class PagosEfectivo(models.Model):
    pagos = models.OneToOneField(Pagos,primary_key=True, unique=True)
    nombre=models.CharField(max_length=50)
    ci=models.CharField(max_length=11)
    
class PagosOtros(models.Model):
    pagos = models.OneToOneField(Pagos,primary_key=True, unique=True)
    nro=models.CharField(max_length=10)
    forma_pago=models.ForeignKey(FormasPago,on_delete=models.PROTECT) 
    
class PagosFacturas(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    pagos=models.ForeignKey(Pagos,on_delete=models.CASCADE)
    facturas=models.ForeignKey(Facturas,on_delete=models.PROTECT)
    importe_pagado=models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    
    def format_importe(self):
        return '{:20,.2f}'.format(self.importe_pagado)
    
class PagosFacturasPart(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    pagos=models.ForeignKey(Pagos,on_delete=models.CASCADE)
    facturas=models.ForeignKey(FacturasParticular,on_delete=models.PROTECT)
    importe_pagado=models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    
    def format_importe(self):
        return '{:20,.2f}'.format(self.importe_pagado)    

class Clientepago(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    cliente =  models.CharField(max_length=100)
    clientep =  models.CharField(max_length=100)
    fecha_pagos = models.DateField()
    moneda = models.CharField(max_length=5)
    forma_pago  = models.CharField(max_length=25)
    importe_pagado = models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    deposito_adelantado =  models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    id_pago=models.CharField(max_length=40)
    
    def __unicode__(self):
        return self.cliente


class Factpago(models.Model):
    id = models.CharField(max_length=40, primary_key=True, unique=True)
    nro =  models.CharField(max_length=10)
    fecha = models.DateField()
    idcliente = models.ForeignKey(Clientepago,on_delete=models.CASCADE)
    imp_pagado=models.DecimalField(max_digits=8, decimal_places=2,default=0.0)
    
class Rep_FacturasxPagar(models.Model):
    id = models.CharField(max_length=40, primary_key=True, unique=True)
    factura_nro=models.CharField(max_length=10)
    fecha_doc=models.DateField()
    nombre=models.CharField(max_length=50)
    organismo=models.CharField(max_length=50)
    provincia=models.CharField(max_length=50)
    precio_mn=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    precio_cuc=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    importe_pagado_cuc=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    importe_pagado_cup=models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    edad=models.IntegerField(default=0)
    
class InvCliente(models.Model):
    year=models.IntegerField(default=0)
    mes=models.IntegerField(default=0)
    cliente=models.ForeignKey(Cliente,on_delete=models.PROTECT)
    cantidad=models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-year','-mes']
        permissions = (("invcliente","invcliente"),)


class FacturasServicios(models.Model):
    doc_factura = models.OneToOneField(Doc, primary_key=True, unique=True)
    factura_nro = models.CharField(max_length=10)
    transportador = models.ForeignKey(Transpotador, on_delete=models.PROTECT)
    cancelada = models.BooleanField(default=False)
    chapa = models.CharField(max_length=10)
    licencia = models.CharField(max_length=10)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    confirmada = models.CharField(max_length=45)
    confirmar = models.BooleanField(default=0)

    def __unicode__(self):
        return self.factura_nro

    class Meta:
        ordering = ['confirmar', 'factura_nro']
        permissions = (("factura", "factura"),)

    def get_importecup(self, *deci):
        importes = self.detallefacturaservicios_set.aggregate(Sum('precio_mn'))
        if len(deci) > 0:
            if importes['precio_mn__sum'] is None:
                return 0
            return importes['precio_mn__sum']
        a1 = 0.00 if importes['precio_mn__sum'] is None else importes['precio_mn__sum']
        return '${:20,.2f}'.format(a1)


    def get_importetotalcup(self, *deci):
        importe_total = self.get_importecup(2)
        if len(deci) > 0:
            return importe_total
        return '${:20,.2f}'.format(importe_total)

    def get_confirmada(self):
        import hashlib
        pkf = self.pk.__str__()

        if self.confirmada == hashlib.sha1(pkf + 'NO').hexdigest():
            return 'N'
        elif self.confirmada == hashlib.sha1(pkf + 'YES').hexdigest():
            return 'S'
        else:
            return 'E'

    def cantidad_servicios(self):
        return self.detallefacturaservicios_set.count()

    def edad_factura(self):
        import datetime
        return (datetime.date.today() - self.doc_factura.fecha_doc).days

    def get_fecha(self):
        fecha = self.doc_factura.fecha_doc
        dia = fecha.day
        mes = fecha.month
        year = fecha.year
        dia1 = '0' + str(dia) if len(str(dia)) < 2 else str(dia)
        mes1 = '0' + str(mes) if len(str(mes)) < 2 else str(mes)
        return dia1 + "/" + mes1 + "/" + str(year)

    def get_renglones(self):
        detallesFact = DetalleFacturaServicios.objects.select_related().filter(factura=self.doc_factura).values('factura',
                                                                                                       'precio_mn',
                                                                                                       'servicio__codigo',
                                                                                                       'servicio__descripcion', \
                                                                                                       'servicio__um__descripcion') \
            .annotate(cantidad=Count('servicio'))

        return detallesFact.__len__()


class DetalleFacturaServicios(models.Model):
    id_detalle = models.CharField(max_length=40, primary_key=True, unique=True)
    factura = models.ForeignKey(FacturasServicios)
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    precio_mn = models.DecimalField(max_digits=18, decimal_places=2, default=0.0)

    def format_precio_mn(self):
        return '{:20,.2f}'.format(self.precio_mn)

class FacturasProdAlter(models.Model):
    doc_factura = models.OneToOneField(Doc, primary_key=True, unique=True)
    factura_nro = models.CharField(max_length=10)
    cancelada = models.BooleanField(default=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    confirmada = models.CharField(max_length=45)
    confirmar = models.BooleanField(default=0)

    def __unicode__(self):
        return self.factura_nro

    class Meta:
        ordering = ['confirmar', 'factura_nro']
        permissions = (("factura", "factura"),)

    def get_importecup(self, *deci):
        importes = self.detallefacturaprodalter_set.aggregate(Sum('importe_mn'))
        if len(deci) > 0:
            if importes['importe_mn__sum'] is None:
                return 0
            return importes['importe_mn__sum']
        a1 = 0.00 if importes['importe_mn__sum'] is None else importes['importe_mn__sum']
        return '${:20,.2f}'.format(a1)


    def get_importetotalcup(self, *deci):
        importe_total = self.get_importecup(2)
        if len(deci) > 0:
            return importe_total
        return '${:20,.2f}'.format(importe_total)

    def get_confirmada(self):
        import hashlib
        pkf = self.pk.__str__()

        if self.confirmada == hashlib.sha1(pkf + 'NO').hexdigest():
            return 'N'
        elif self.confirmada == hashlib.sha1(pkf + 'YES').hexdigest():
            return 'S'
        else:
            return 'E'

    def cantidad_producciones(self):
        return self.detallefacturaprodalter_set.count()

    def edad_factura(self):
        import datetime
        return (datetime.date.today() - self.doc_factura.fecha_doc).days

    def get_fecha(self):
        fecha = self.doc_factura.fecha_doc
        dia = fecha.day
        mes = fecha.month
        year = fecha.year
        dia1 = '0' + str(dia) if len(str(dia)) < 2 else str(dia)
        mes1 = '0' + str(mes) if len(str(mes)) < 2 else str(mes)
        return dia1 + "/" + mes1 + "/" + str(year)

    def get_renglones(self):
        detallesFact = DetalleFacturaProdAlter.objects.select_related().filter(factura=self.doc_factura).values('factura',
                                                                                                       'precio_mn',
                                                                                                       'produccionalter__codigo',
                                                                                                       'produccionalter__descripcion', \
                                                                                                       'produccionalter__um__descripcion') \
            .annotate(cantidad=Count('produccionalter'))

        return detallesFact.__len__()

class DetalleFacturaProdAlter(models.Model):
    id_detalle = models.CharField(max_length=40, primary_key=True, unique=True)
    factura = models.ForeignKey(FacturasProdAlter)
    produccionalter = models.ForeignKey(ProdAlter, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    precio_mn = models.DecimalField(max_digits=18, decimal_places=2, default=0.0)
    importe_mn = models.DecimalField(max_digits=18, decimal_places=2, default=0.0)

    def format_precio_mn(self):
        return '{:20,.2f}'.format(self.precio_mn)

    def format_importe_mn(self):
        return '{:20,.2f}'.format(self.importe_mn)

    def format_cantidad(self):
        return '{:20,.2f}'.format(self.cantidad)


