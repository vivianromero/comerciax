#-*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from comerciax.admincomerciax.models import *
#from comerciax.comercial.models import Facturas,DetalleFactura
from comerciax import admincomerciax
from django.contrib.contenttypes.models import ContentType
from comerciax.utils import Estados, Meses
import datetime


# Estos van el admin

'''
Inventario de Cierre
'''
class Invcierre(models.Model):
    id=models.CharField(max_length=40,primary_key=True, unique=True)
    year=models.CharField(max_length=4)
    mes=models.CharField(max_length=15)
    medida=models.ForeignKey(Producto,on_delete=models.PROTECT)
    almcasco=models.IntegerField(default=0)
    almproduccion=models.IntegerField(default=0)
    almprodterminada=models.IntegerField(default=0)

class Invalmacencasco(models.Model):
    id=models.CharField(max_length=40,primary_key=True, unique=True)
    year=models.IntegerField(default=0)
    mes=models.IntegerField(default=0)
    medida=models.ForeignKey(Producto,on_delete=models.PROTECT)
    almacen=models.IntegerField(default=0)
    dvp=models.IntegerField(default=0)
    dip=models.IntegerField(default=0)
    er=models.IntegerField(default=0)
    ree=models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-year','-mes']
        permissions = (("invalmcasco","invalmcasco"),)

class Invalmacenprod(models.Model):
    id=models.CharField(max_length=40,primary_key=True, unique=True)
    year=models.IntegerField(default=0)
    mes=models.IntegerField(default=0)
    medida=models.ForeignKey(Producto,on_delete=models.PROTECT)
    produccion=models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-year','-mes']
        permissions = (("invalmprod","invalmprod"),)
    
class Invalmacenprodterm(models.Model):
    id=models.CharField(max_length=40,primary_key=True, unique=True)
    year=models.IntegerField(default=0)
    mes=models.IntegerField(default=0)
    medida=models.ForeignKey(Producto,on_delete=models.PROTECT)
    pt=models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-year','-mes']
        permissions = (("invalmprodt","invalmprodt"),)

class Balancecascovsrecap(models.Model):
    year=models.IntegerField(default=0)
    mes=models.IntegerField(default=0)
    medida=models.CharField(max_length=40)
    invini=models.IntegerField(default=0)
    casco=models.IntegerField(default=0)
    er=models.IntegerField(default=0)
    ree=models.IntegerField(default=0)
    ecr=models.IntegerField(default=0)
    dip=models.IntegerField(default=0)
    fact=models.IntegerField(default=0)
    tranf=models.IntegerField(default=0)
    balance=models.IntegerField(default=0)
    invf=models.IntegerField(default=0)
    dif=models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-year','-mes']
        permissions = (("invalmprodt","invalmprodt"),)



'''
Se lleva el control de los numeros
'''

class Cierre(models.Model):
    id=models.CharField(max_length=40,primary_key=True, unique=True)
    fechacierre=models.DateField()
    
class NumeroDoc(models.Model):
    id_numerodoc=models.CharField(max_length=40,primary_key=True, unique=True)
    #nro_nominaz= models.CharField(max_length=10,null=True)
    #nro_minaz=models.CharField(max_length=10,null=True)
    nro_oferta=models.IntegerField(default=0)
    nro_factura=models.IntegerField(default=0)
    nro_facturapart=models.IntegerField(default=0)
    nro_facturaext=models.IntegerField(default=0)
    


''' 
Donde se guardan los datos generales de los documentos de entrada y salida
'''
class Doc(models.Model):
    id_doc=models.CharField(max_length=40,primary_key=True, unique=True)
    fecha_doc=models.DateField()
    operador=models.ForeignKey(User,on_delete=models.PROTECT)
    fecha_operacion=models.DateTimeField(auto_now=True)
    # Aqui se guarda el origen del Documento 
    # 1-Recepcion de cascos a clientes
    # 2-Entrega de cascos a produccion
    # 3-Recepcion de cascos a clientes externos
    # 4-Devolucion de Cascos a Inservible
    # 5-Devolucion de Cascos a Vulca
    # 6-Trnasferencia de Casco a Ent. Externas
    # 7-Rechazado por error de Recepcion
    # 8-Entrega de cascos rechazados
    # 9-Produccion Terminada
    # 10- Recepc. de pt desde entidades externas
    # 11- Recepc. de rechazados desde entidades externas
    # 12- Entrega de vulca a produccion
    # 13 - Oferta
    # 14 - Factura
    # 15 - Decomisar Cascos
    # 16 - Recepcion de Casco a particulares
    # 17 - Factura a particulares
    # 18- Recepc. de Casco desde entidades externas, transf. no aceptada
    # 19- Devolucion de casco a clientes
    
    tipo_doc=models.CharField(max_length=2) 
    
    observaciones=models.TextField(blank=True)

    
''' 
Datos del casco
''' 
class CascoManager(models.Manager):
    def get_by_natural_key(self,id_casco,casco_nro,id,descripcion):
        return self.get(
            id_casco=id_casco,
            casco_nro=casco_nro,
            producto=Producto.objects.get_by_natural_key(id,descripcion),
            producto_salida=Producto.objects.get_by_natural_key(id,descripcion)
        )

class Casco(models.Model):
    objects = CascoManager()
    id_casco=models.CharField(max_length=40, primary_key=True, unique=True)
    casco_nro=models.IntegerField()
    producto=models.ForeignKey(Producto,related_name = 'MedidaEntrada',verbose_name='Medida Entrada',on_delete=models.PROTECT)
    estado_actual=models.CharField(max_length=30)
    venta=models.BooleanField(default=False)
    producto_salida=models.ForeignKey(Producto,related_name = 'MedidaSalida',verbose_name='Medida Salida',on_delete=models.PROTECT)
    particular=models.BooleanField(default=False)
    decomisado=models.BooleanField(default=False)
    id_cliente=models.ForeignKey(Cliente,related_name = 'Cliente',verbose_name='Cliente',on_delete=models.PROTECT,null=True)
    fecha=models.DateField(null=True)
    ocioso=models.BooleanField(default=False)
    
    def natural_key(self):
        return (self.id_casco,self.casco_nro, )+ self.producto.natural_key()
        #return (self.id_casco,self.casco_nro)
    natural_key.dependencies = ['admincomerciax.producto']
    
    class Meta:
        unique_together = (('id_casco', 'casco_nro'),)
        permissions = (("casco","casco"),)
    def __unicode__(self):
        return self.casco_nro
    
    def get_estado_actual(self):
        return Estados.estados[self.estado_actual]
    
    def get_cliente(self):        
        "Retornar el cliente."
        if DetalleRC.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleRC.objects.get(casco=self.id_casco).rc.cliente.nombre
        return "**"+DetalleRP.objects.get(casco=self.id_casco).rp.nombre
    
    def get_idcliente(self):        
        "Retornar el id cliente."
        if DetalleRC.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleRC.objects.get(casco=self.id_casco).rc.cliente.id
    
    def get_trans_para(self):        
        "Retornar para donde se transfirio el casco."
        if DetalleTransferencia.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleTransferencia.objects.get(casco=self.id_casco).transf.destino.id
        
    def get_cliente_organismo(self):        
        "Retornar el cliente."
        if DetalleRC.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleRC.objects.get(casco=self.id_casco).rc.cliente.organismo.siglas_organismo
        return "** No Estatal"
    
    def get_cliente_provincia(self):        
        "Retornar el cliente."
        if DetalleRC.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleRC.objects.get(casco=self.id_casco).rc.cliente.provincia.descripcion_provincia
        return ""
    
    def get_fechaentrada(self):
        if DetalleRC.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleRC.objects.get(casco=self.id_casco).rc.doc_recepcioncliente.fecha_doc
        return DetalleRP.objects.get(casco=self.id_casco).rp.doc_recepcionparticular.fecha_doc
    
    def get_documento(self):
        if DetalleRC.objects.filter(casco=self.id_casco).count()!=0:
            return DetalleRC.objects.get(casco=self.id_casco).rc.recepcioncliente_nro
        return DetalleRP.objects.get(casco=self.id_casco).rp.recepcionparticular_nro
    
    def get_causa_rechazo(self):
        if self.estado_actual=="DIP":
            return DetalleDIP.objects.get(casco=self.id_casco).causa.descripcion
        elif self.estado_actual=="ER":
            iddetalle=Detalle_ER.objects.get(casco=self.id_casco).id_detalleer
            causa="Error de revisión"
            caus=CausaRechazo_ER.objects.filter(detalle_er=iddetalle)
            if caus.__len__()!=0:
                c1=CausaRechazo_ER.objects.get(detalle_er=iddetalle).causa.descripcion
                causa = c1 if c1.__len__()!=0 else causa
            return causa
        elif self.estado_actual=="REE":
            iddetalle=DetalleRRE.objects.get(casco=self.id_casco).id_detallerre
            causa="Rechazado por entidades externa"
            caus=CausaRechazoRRE.objects.filter(detalle_rre=iddetalle) 
            if caus.__len__()!=0:
                c1=CausaRechazoRRE.objects.get(detalle_rre=iddetalle).causa.descripcion
                causa = c1 if c1.__len__()!=0 else causa
            return causa
        return ""
    
    def get_dias(self):
#    
        if self.estado_actual=='Casco' and self.particular==False:
            fecha=DetalleRC.objects.get(casco=self.id_casco).rc.doc_recepcioncliente.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='Casco' and self.particular==True:
            fecha=DetalleRP.objects.get(casco=self.id_casco).rp.doc_recepcionparticular.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='Produccion':
            detallecc=DetalleCC.objects.get(casco=self.id_casco).cc.doc_cc
            fecha=detallecc.fecha_doc
            detallevp=DetalleVP.objects.filter(casco=self.id_casco)
#            vp.doc_vulcaproduccion
            for ax in detallevp:
                fecha2=ax.vp.doc_vulcaproduccion.fecha_doc
                if fecha2>fecha:
                    fecha=fecha2
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='PT':
            if DetallePT.objects.filter(casco=self.id_casco).count()!=0:
                fecha=DetallePT.objects.get(casco=self.id_casco).pt.doc_pt.fecha_doc
            else:
                try:
                    fecha=DetallePTE.objects.get(casco=self.id_casco).doc_pte.doc_ptexternos.fecha_doc
                except Exception, e:
                    return 0
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='Transferencia':
            fecha=DetalleTransferencia.objects.get(casco=self.id_casco).transf.doc_transferencia.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='DIP':
            fecha=DetalleDIP.objects.get(casco=self.id_casco).dip.doc_dip.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='DVP':
            detalledvp=DetalleDVP.objects.filter(casco=self.id_casco)
            iter=0
            for ax in detalledvp:
                if iter==0:
                    fecha=ax.dvp.doc_dvp.fecha_doc
                if ax.dvp.doc_dvp.fecha_doc > fecha:
                    fecha=ax.dvp.doc_dvp.fecha_doc
                iter+=1
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='ER':
            fecha=Detalle_ER.objects.get(casco=self.id_casco).errro_revision.doc_errorrecepcion.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='ECR':
            fecha=DetalleEntregaRechazado.objects.get(casco=self.id_casco).erechazado.doc_entregarechazado.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='REE':
            fecha=DetalleRRE.objects.get(casco=self.id_casco).receprechaext.doc_receprechaext.fecha_doc
            return (datetime.date.today() - fecha).days
        if self.estado_actual=='DC':
            fecha=Detalle_DC.objects.get(casco=self.id_casco).doc_decomiso.doc_decomiso.fecha_doc
            return (datetime.date.today() - fecha).days
        return ""
#        if self.estado_actual==unicode(Estados.estados['Factura'],'utf-8'):
#            fecha=DetalleFactura.objects.get(casco=self.id_casco).receprechaext.doc_receprechaext.fecha_doc
#            return datetime.date.today() - fecha
        
'''
recepcion de cascos a particulares
'''
  
class RecepcionParticular(models.Model):
    doc_recepcionparticular=models.OneToOneField(Doc,primary_key=True, unique=True)
    recepcionparticular_nro = models.CharField(max_length=4)
    #cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    nombre = models.CharField(max_length=50)
    ci = models.CharField(max_length=11)
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('V', 'Para la Venta'),
        ('O','Otro')
    )
    recepcionparticular_tipo=models.CharField(max_length=1, choices=TIPO_CHOICES)
    procesado=models.BooleanField(default=False)
    #recepcioncliente_ajuste=models.BooleanField(default=False)
    def __unicode__(self):
        return self.nombre
    class Meta:
        ordering = ['recepcionparticular_nro']
        permissions = (("recepcioncliente","recepcioncliente"),)
    

class DetalleRP(models.Model):
    id_detallerp=models.CharField(max_length=40, primary_key=True, unique=True)
    rp = models.ForeignKey(RecepcionParticular)
    casco = models.ForeignKey(Casco)
    
    class Meta:
        unique_together = (('rp', 'casco'),)  

'''
recepcion de cascos a clientes
'''
  
class RecepcionCliente(models.Model):
    doc_recepcioncliente=models.OneToOneField(Doc,primary_key=True, unique=True)
    recepcioncliente_nro = models.CharField(max_length=4)
    #cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    TIPO_CHOICES = (
        ('A', 'Ajuste'),
        ('V', 'Para la Venta'),
        ('O','Otro')
    )
    recepcioncliente_tipo=models.CharField(max_length=1, choices=TIPO_CHOICES)
    procesado=models.BooleanField(default=False)
    #recepcioncliente_ajuste=models.BooleanField(default=False)
    def __unicode__(self):
        return self.ptexternos_nro
    
    
    class Meta:
        ordering = ['recepcioncliente_nro']
        permissions = (("recepcioncliente","recepcioncliente"),)
        
class DetalleRC(models.Model):
    id_detallerc=models.CharField(max_length=40, primary_key=True, unique=True)
    rc = models.ForeignKey(RecepcionCliente)
    casco = models.ForeignKey(Casco)
    nro_externo = models.CharField(max_length=10, blank=True)
    
    class Meta:
        unique_together = (('rc', 'casco'),)
        
    def get_cantidad_casco(self):  
        return DetalleRC.objects.select_related().filter(rc=self.rc).count()
   
'''
recepcion de cascos rechazados por entidades externas
'''
class RecepRechaExt(models.Model):
    doc_receprechaext = models.OneToOneField(Doc,primary_key=True, unique=True)
    receprechaext_nro = models.CharField(max_length=4)
    nro_factura = models.CharField(max_length=10)
    cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.receprechaext_nro
    class Meta:
        permissions = (("receprechext","receprechext"),)

class DetalleRRE(models.Model):
    id_detallerre=models.CharField(max_length=40, primary_key=True, unique=True)
    receprechaext = models.ForeignKey(RecepRechaExt)
    casco = models.ForeignKey(Casco)
    nro_externo = models.CharField(max_length=10)
    #causa=models.ForeignKey(CausasRechazo, verbose_name = 'Causa de Rechazo',on_delete=models.PROTECT)
    class Meta:
        unique_together = (('receprechaext', 'casco'),)
        
class RecepCascoExt(models.Model):
    doc_recepcascoext = models.OneToOneField(Doc,primary_key=True, unique=True)
    recepcascoext_nro = models.CharField(max_length=4)
    nro_factura = models.CharField(max_length=10)
    cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.recepcascoext_nro
    class Meta:
        permissions = (("recepcascoext","recepcascoext"),)

class DetalleRCE(models.Model):
    id_detallerce=models.CharField(max_length=40, primary_key=True, unique=True)
    recepcascoext = models.ForeignKey(RecepCascoExt)
    casco = models.ForeignKey(Casco)
    nro_externo = models.CharField(max_length=10)
    #causa=models.ForeignKey(CausasRechazo, verbose_name = 'Causa de Rechazo',on_delete=models.PROTECT)
    class Meta:
        unique_together = (('recepcascoext', 'casco'),)

class CausaRechazoRRE(models.Model):
    detalle_rre = models.OneToOneField(DetalleRRE, primary_key=True, unique=True)
    causa = models.ForeignKey(CausasRechazo,on_delete=models.PROTECT)
    class Meta:
        permissions = (("causarechext","causarechext"),)

'''
devolucion de produccion a inservibles
'''

class DIP(models.Model):
    doc_dip=models.OneToOneField(Doc,primary_key=True, unique=True)
    nro_dip=models.CharField(max_length=10)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.nro_dip
    class Meta:
        permissions = (("dip","dip"),)


class DetalleDIPManager(models.Manager):
    def get_by_natural_key(self,id_detalledip,descripcion,descripcioncausa):
        return self.get(
            id_detalledip=id_detalledip,
            area=Area.objects.get_by_natural_key(descripcion),
            causa=CausasRechazo.objects.get_by_natural_key(descripcioncausa)
        )
        
class DetalleDIP(models.Model):
    objects = DetalleDIPManager()
    id_detalledip=models.CharField(max_length=40, primary_key=True, unique=True)
    dip = models.ForeignKey(DIP)
    casco = models.ForeignKey(Casco)
    causa = models.ForeignKey(CausasRechazo,on_delete=models.PROTECT)
    area = models.ForeignKey(Area,on_delete=models.PROTECT)
    reponsable = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = (('dip', 'casco'),)
    def natural_key(self):
        #return (self.id_casco,self.casco_nro, ) + self.producto.natural_key()
        #return (self.id_casco,self.casco_nro, ) + self.producto.natural_key()
        return (self.id_detalledip, )+ self.area.natural_key() + self.causa.natural_key()
    
    natural_key.dependencies = ['admincomerciax.area','admincomerciax.causasrechazo']


'''
devolucion de prod.a vulca
'''

class DVP(models.Model):
    doc_dvp=models.OneToOneField(Doc,primary_key=True, unique=True)
    nro_dvp=models.CharField(max_length=10)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.nro_dvp
    class Meta:
        permissions = (("dvp","dvp"),)

class DetalleDVP(models.Model):
    id_detalledvp=models.CharField(max_length=40, primary_key=True, unique=True)
    dvp = models.ForeignKey(DVP)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('dvp', 'casco'),)

''' 
Transferencia de cascos para entidades externas para ser recapados
'''    
class Transferencia(models.Model):
    doc_transferencia = models.OneToOneField(Doc,primary_key=True, unique=True)
    transferencia_nro = models.CharField(max_length=4)
    destino = models.ForeignKey(Cliente, verbose_name = 'Destino',on_delete=models.PROTECT)
    cerrada=models.BooleanField(default=False)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.transferencia_nro
    class Meta:
        permissions = (("transferencia","transferencia"),)

class DetalleTransferencia(models.Model):
    id_detalletransferencia=models.CharField(max_length=40, primary_key=True, unique=True)
    transf = models.ForeignKey(Transferencia)
    casco = models.ForeignKey(Casco)
    id_docrecepc = models.CharField(max_length=40, blank=True)
    rechazado=models.BooleanField(default=False)
    
    class Meta:
        unique_together = (('transf', 'casco'),)


'''
cascos que se recepcionaron y antes de pasar a produccion se rechazaron
en la revision inicial no se rechazaron
'''

class ErrorRecepcion(models.Model):
    doc_errorrecepcion=models.OneToOneField(Doc,primary_key=True, unique=True)
    procesado=models.BooleanField(default=False)
    class Meta:
        permissions = (("errorrecep","errorrecep"),)
    
class Detalle_ER(models.Model):
    id_detalleer=models.CharField(max_length=40, primary_key=True, unique=True)
    errro_revision=models.ForeignKey(ErrorRecepcion)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('errro_revision', 'casco'),)
   
'''
El error de recepcion puede o no tener la causa de rachazo, por lo que se hace la sgte relacion
'''

    
class CausaRechazo_ER(models.Model):
    detalle_er = models.OneToOneField(Detalle_ER, primary_key=True, unique=True)
    causa = models.ForeignKey(CausasRechazo,on_delete=models.PROTECT)

''' 
Devolucion de cacos a clientes
'''    
class DevolucionCasco(models.Model):
    doc_devolucion = models.OneToOneField(Doc,primary_key=True, unique=True)
    devolucion_nro = models.CharField(max_length=4)
    cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.devolucion_nro
    class Meta:
        permissions = (("devolucion","devolucion"),)

class DetalleDCC(models.Model):
    id_detalle=models.CharField(max_length=40, primary_key=True, unique=True)
    devolucion = models.ForeignKey(DevolucionCasco)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('devolucion', 'casco'),)
''' 
Entrega de cascos rechazados a clientes
'''    
class EntregaRechazado(models.Model):
    doc_entregarechazado = models.OneToOneField(Doc,primary_key=True, unique=True)
    entregarechazado_nro = models.CharField(max_length=4)
    cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.entregarechazado_nro
    class Meta:
        permissions = (("entregrech","entregrech"),)

class DetalleEntregaRechazado(models.Model):
    id_detalleer=models.CharField(max_length=40, primary_key=True, unique=True)
    erechazado = models.ForeignKey(EntregaRechazado)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('erechazado', 'casco'),)
 
''' 
Entrega de cascos a produccion
'''   
class CC(models.Model):
    doc_cc = models.OneToOneField(Doc,primary_key=True, unique=True)
    cc_nro = models.CharField(max_length=4)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.cc_nro
    class Meta:
        permissions = (("cc","cc"),)

class DetalleCC(models.Model):
    id_detallecc=models.CharField(max_length=40, primary_key=True, unique=True)
    cc = models.ForeignKey(CC)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('cc', 'casco'),)

'''
Entrega desde vulca a produccion 
'''
class VulcaProduccion(models.Model):
    doc_vulcaproduccion = models.OneToOneField(Doc,primary_key=True, unique=True)
    vulcaproduccion_nro = models.CharField(max_length=4)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.vulcaproduccion_nro
    class Meta:
        permissions = (("vulcaprod","vulcaprod"),)

class DetalleVP(models.Model):
    id_detallevp=models.CharField(max_length=40, primary_key=True, unique=True)
    vp = models.ForeignKey(VulcaProduccion)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('vp', 'casco'),)

# Produccion terminada
''' 
Entrega de cascos de produccion a produccion terminada
'''
class ProduccionTerminada(models.Model):
    doc_pt = models.OneToOneField(Doc,primary_key=True, unique=True)
    produccionterminada_nro = models.CharField(max_length=4)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.produccionterminada_nro
    class Meta:
        permissions = (("prodterm","prodterm"),)

class DetallePT(models.Model):
    id_detallept=models.CharField(max_length=40, primary_key=True, unique=True)
    pt = models.ForeignKey(ProduccionTerminada)
    casco = models.ForeignKey(Casco)
    class Meta:
        unique_together = (('pt', 'casco'),)

''' 
recepcion de cascos en produccion terminada de entidades externas
'''

class PTExternos(models.Model):
    doc_ptexternos = models.OneToOneField(Doc,primary_key=True, unique=True)
    ptexternos_nro = models.CharField(max_length=4)
    cliente = models.ForeignKey(Cliente, verbose_name = 'Cliente',on_delete=models.PROTECT)
    nro_factura = models.CharField(max_length=10,blank=True)
    procesado=models.BooleanField(default=False)
    def __unicode__(self):
        return self.ptexternos_nro
    class Meta:
        permissions = (("ptext","ptext"),)

class DetallePTE(models.Model):
    id_detallepte=models.CharField(max_length=40, primary_key=True, unique=True)
    doc_pte = models.ForeignKey(PTExternos)
    casco = models.ForeignKey(Casco)
    nro_externo = models.CharField(max_length=10,blank=True)
    class Meta:
        unique_together = (('doc_pte', 'casco'),)
    
   
''' 
Trazabilidad del casco
'''

class TrazabilidadCasco(models.Model):
    id_trazabilidad=models.CharField(max_length=40, primary_key=True, unique=True)
    nro=models.PositiveIntegerField()
    #casco = models.ForeignKey(Casco,on_delete=models.PROTECT)
    casco = models.ForeignKey(Casco)
    estado = models.CharField(max_length=30)
    activo=models.BooleanField(default=True)
    #doc=models.ForeignKey(Doc,on_delete=models.PROTECT)
    doc=models.ForeignKey(Doc)
    
'''
rechazo revision
'''
class RechazadoRevision(models.Model):
    id_rechazorevision=models.CharField(max_length=40, primary_key=True, unique=True)
    cliente=models.ForeignKey(Cliente,on_delete=models.PROTECT)
    fecha=models.DateField()
    operdor=models.ForeignKey(User,on_delete=models.PROTECT)
    fecha_operacion=models.DateTimeField(auto_now=True)
    observaciones=models.TextField(blank=True)
    procesado=models.BooleanField(default=False)
    class Meta:
        permissions = (("rechrev","rechrev"),)

class Detalle_RechazadoRevision(models.Model):
    id_detalleRR=models.CharField(max_length=40, primary_key=True, unique=True)
    rechazado_revision=models.ForeignKey(RechazadoRevision)
    producto=models.ForeignKey(Producto,on_delete=models.PROTECT)
    cantidad=models.IntegerField()


'''
cascos que llevan mas de x dias en PT y son decomisados al cliente

'''
class CascoDecomiso(models.Model):
    doc_decomiso=models.OneToOneField(Doc,primary_key=True, unique=True)
    dias=models.IntegerField()
    procesado=models.BooleanField(default=False)
    class Meta:
        permissions = (("decomisar","decomisar"),)
    
class Detalle_DC(models.Model):
    id_detalledc=models.CharField(max_length=40, primary_key=True, unique=True)
    doc_decomiso=models.ForeignKey(CascoDecomiso)
    casco = models.ForeignKey(Casco)
    dias = models.IntegerField()

class Fechacierre(models.Model):
    year=models.IntegerField(default=0)
    mes=models.IntegerField(default=0)
    almacen=models.CharField(max_length=2)
    
    class Meta:
        permissions = (("cierremes","cierremes"),)
    '''
    la tabla de inicializarse con el mes anterior de los datos que se estan introduciendo
       c - almacen de casco
       p - almacen de produccion
       pt - almacen de produccion terminada 
       cm - almacen comercial
    '''
    def fechaminima(self):
        if self.mes==12:
            return '1/'+'1/'+str(self.year+1)
        return '1/'+str(self.mes+1)+'/'+str(self.year)
            
    def fechamaxima(self):
        if self.mes==12:
            return '30/'+'1/'+str(self.year+1)
        if self.mes==1:
            if (self.year%400==0 or self.year%100==0 or self.year%4==0):
                return '29/2/'+str(self.year) # es ano bisiesto
            else:
                return '28/2/'+str(self.year)
        return Meses.meses[self.mes+1]+'/'+str(self.mes+1)+'/'+str(self.year)   