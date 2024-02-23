from django.db import models
import base64
'''
Created on Mar 15, 2011

@author: jesus
'''
from django.utils.encoding import smart_str
from comerciax.utils import Estados, Meses
from django.db.models.sql.constants import NULLABLE
import datetime
from comerciax.utils import * 
#from comerciax.casco.models import Fechacierre

class Provincias(models.Model):
    codigo_provincia=models.CharField(max_length=40,primary_key=True, unique=True)
    descripcion_provincia= models.CharField(max_length=20, unique=True)
#    slug = models.SlugField(editable=True)
    def __unicode__(self):
        return self.descripcion_provincia
    class Meta:
        ordering = ['descripcion_provincia']
        permissions = (("provincias","provincias"),)

class Organismo(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    codigo_organismo=models.CharField(max_length=3, unique=True)
    siglas_organismo=models.CharField('Siglas',max_length=35,unique=True)
    
    def __unicode__(self):
        return self.siglas_organismo
    class Meta:
        ordering = ['siglas_organismo']
        permissions = (("organismo","organismo"),)
        
class Union(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion= models.CharField(max_length=20, unique=True)
    organismo=models.ForeignKey(Organismo)
    
    def __unicode__(self):
        return self.descripcion
    class Meta:
        ordering = ['descripcion']

class Sucursales(models.Model):
    id_sucursal=models.CharField(max_length=40, primary_key=True, unique=True)
    sucursal_descripcion=models.CharField(max_length=15,unique=True)
    def __unicode__(self):
        return self.sucursal_descripcion
    class Meta:
        ordering = ['sucursal_descripcion']
        permissions = (("sucursal","sucursal"),)

class Cliente(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    organismo=models.ForeignKey(Organismo,on_delete=models.PROTECT)
    union=models.ForeignKey(Union,on_delete=models.PROTECT,null=True)
    provincia=models.ForeignKey(Provincias,verbose_name = 'Provincia',on_delete=models.PROTECT)
    codigo=models.CharField('C&oacute;digo Empresa',max_length=14) # Organismo.Subordinacion.CodigoEmpresa ---.-.-------- 
    nombre=models.CharField('Nombre de la Empresa',max_length=50)
    direccion=models.TextField('Direcci&oacute;n',max_length=200)
    fax=models.CharField('Fax',max_length=50, null=True, blank=True)
    email=models.EmailField('E-mail', null=True, blank=True)
    telefono=models.CharField('Tel&eacute;fono',max_length=50, null=True, blank=True)
    externo=models.BooleanField(default=False)
    eliminado=models.BooleanField(default=False)
    comercializadora=models.BooleanField(default=False)
    def __unicode__(self):
        return u"%s | %s" % (self.codigo, self.nombre)
             
    class Meta:
        ordering = ['codigo']
        permissions = (("cliente","cliente"),)

        
    def eliminar(self):
        self.eliminado = True
        self.save()
        if ClienteContrato.objects.select_related().filter(cliente=self.id,cerrado=False).count()!=0:
            idcontrato=ClienteContrato.objects.get(cliente=self.id,cerrado=False).contrato.id_contrato
            ClienteContrato.objects.get(cliente=self.id,cerrado=False).delete()
            if ClienteContrato.objects.select_related().filter(contrato=idcontrato).count()==0:
                Contrato.objects.get(id_contrato=idcontrato).delete()
#            Transpotador.objects.filter(contrato=idcontrato).update(activo=False)
#            Representante.objects.filter(contrato=idcontrato).update(activo=False)
        
    def get_contrato_dias(self):
        return (ClienteContrato.objects.get(cliente=self.id, cerrado=False).contrato.fecha_vencimiento-datetime.date.today()).days
    
    def get_contrato_tipo(self):
        "Retornar el cliente."
#        ClienteContrato.objects.select_related().get(cliente=self.id, contrato__cerrado=False)
#        ClienteContrato.objects.select_related().get(cliente=self.id, contrato__cerrado=False).contrato
        return ClienteContrato.objects.select_related().get(cliente=self.id, cerrado=False).contrato.para_la_venta
    
    def get_contrato_tipoDesc(self):
        "Retornar el cliente."
        if ClienteContrato.objects.select_related().get(cliente=self.id,cerrado=False).contrato.para_la_venta==True:
            return "De Venta"
        else:
            return "Normal"
    
    def get_contrato_preciocup(self):
        "Retornar el cliente."
        if ClienteContrato.objects.select_related().get(cliente=self.id,cerrado=False).contrato.preciomn==True:
            return "De Venta"
        else:
            if ClienteContrato.objects.select_related().get(cliente=self.id,cerrado=False).contrato.preciocostomn==True:
                return "De Costo"
        return "No Existe"
    
    def get_contrato_preciocuc(self):
        "Retornar el cliente."
        if ClienteContrato.objects.select_related().get(cliente=self.id,cerrado=False).contrato.preciocuc==True:
            return "De Venta"
        else:
            if ClienteContrato.objects.select_related().get(cliente=self.id,cerrado=False).contrato.preciocostocuc==True:
                return "De Costo"
        return "No Existe"
    
    def get_contrato_nro(self):
        "Retornar el numero de contrato."
        numero=ClienteContrato.objects.select_related().filter(cliente=self.id, cerrado=False)
        numero_cont="Sin Contrato"
        if numero.__len__()==0:
            return numero_cont
        for a1 in numero:
            numero_cont=a1.contrato.contrato_nro
#        numero=ClienteContrato.objects.select_related().get(cliente=self.id, contrato__cerrado=False)
#        numero_cont=numero[0] 
        return numero_cont
    
    def get_idcontrato(self):
        "Retornar el id de contrato."
        id=ClienteContrato.objects.select_related().filter(cliente=self.id, cerrado=False)
        id_cont="1"
        if id.__len__()==0:
            return id_cont
        for a1 in id:
            id_cont=a1.contrato.id_contrato
#        numero=ClienteContrato.objects.select_related().get(cliente=self.id, contrato__cerrado=False)
#        numero_cont=numero[0] 
        return id_cont
    
    def get_precio_casco(self):
        "Retornar el id de contrato."
        id=ClienteContrato.objects.select_related().filter(cliente=self.id, cerrado=False)
        id_cont="1"
        if id.__len__()==0:
            return False
        for a1 in id:
            return a1.contrato.otro_precio_casco
    
    def get_plan_contratado(self,ano):
        plan_contratado=0
        id_cont=self.get_idcontrato()
        if id_cont=='1':
            return plan_contratado
        
        objeto=Planes.objects.filter(contrato=id_cont,plan_ano=ano)  
        for objects in objeto:
            plan_contratado=objects.plan_contratado
        return plan_contratado
    
    
    def get_facturas_porpagar(self):
        '''
        Devolver las facturas por pagar de un cliente 
        lo devuelve en una lista de dicc con los campos llaves
        pk nro importecuc importecup
        '''
        from comerciax.comercial.models import Facturas
        import hashlib
        fact=Facturas.objects.filter(cliente=self).exclude(tipo = 'A')
        lista_facturas=[]
        for factu in fact:
            
            porpagarcup=0 if factu.get_porpagar_cup(1)== None else factu.get_porpagar_cup(1)
            if factu.confirmada==hashlib.sha1(factu.pk.__str__()+'YES').hexdigest() and porpagarcup != 0:
                return True
            porpagarcuc=0 if factu.get_porpagar_cuc(1)== None else factu.get_porpagar_cuc(1)
            if factu.confirmada==hashlib.sha1(factu.pk.__str__()+'YES').hexdigest() and porpagarcuc != 0:
                return True
                #lista_facturas=lista_facturas+[{"pk":factu.doc_factura.id_doc,"nro":factu.factura_nro,"importecuc":'{:20,.2f}'.format(porpagarcuc),"importecup":'{:20,.2f}'.format(porpagarcuc)}]
            
        return False

     
    def get_cuenta_porpagar(self):
        '''
        Devuelve 0 si no tiene_cuenta_por_pagar y 1 si tiene cuenta por pagar 
        '''
        from comerciax.comercial.models import Facturas
        import hashlib
        fact=Facturas.objects.filter(cliente=self).exclude(tipo = 'A')
        lista_facturas=[]
        for factu in fact:
            porpagarcuc=0 if factu.get_porpagar_cuc(1)== None else factu.get_porpagar_cuc(1)
            porpagarcup=0 if factu.get_porpagar_cup(1)== None else factu.get_porpagar_cup(1)
            if factu.confirmada==hashlib.sha1(factu.pk.__str__()+'YES').hexdigest() and porpagarcuc+porpagarcup != 0:
                return 1
        return 0
        
    def get_facturas_porpagarcup(self):
        '''
        Devolver las facturas por pagar en CUP de un cliente 
        lo devuelve en una lista de dicc con los campos llaves
        pk nro importe
        '''
        from comerciax.comercial.models import Facturas
        import hashlib
        fact=Facturas.objects.filter(cliente=self).exclude(tipo = 'A').order_by('factura_nro')
        lista_facturas=[]
        for factu in fact:
            porpagarcup=0 if factu.get_porpagar_cup(1)== None else factu.get_porpagar_cup(1)
#            porpagarcup=0 if factu.get_porpagar_cup(1)== None else factu.get_porpagar_cup(1)
            if factu.confirmada==hashlib.sha1(factu.pk.__str__()+'YES').hexdigest() and porpagarcup != 0:
                lista_facturas=lista_facturas+[{"pk":factu.doc_factura.id_doc,"nro":factu.factura_nro,"imp_num":str(porpagarcup),"importe":'{:20,.2f}'.format(porpagarcup)}]   
        return lista_facturas

    
    def get_facturas_porpagarcuc(self):
        '''
        Devolver las facturas por pagar en CUC de un cliente 
        lo devuelve en una lista de dicc con los campos llaves
        pk nro importe
        '''
        from comerciax.comercial.models import Facturas
        import hashlib
        fact=Facturas.objects.filter(cliente=self).exclude(tipo = 'A').order_by('factura_nro')
        lista_facturas=[]
        for factu in fact:
            porpagarcuc=0 if factu.get_porpagar_cuc(1)== None else factu.get_porpagar_cuc(1)
#            porpagarcup=0 if factu.get_porpagar_cup(1)== None else factu.get_porpagar_cup(1)
            if factu.confirmada==hashlib.sha1(factu.pk.__str__()+'YES').hexdigest() and porpagarcuc != 0:
                lista_facturas=lista_facturas+[{"pk":factu.doc_factura.id_doc,"nro":factu.factura_nro,"imp_num":str(porpagarcuc),"importe":'{:20,.2f}'.format(porpagarcuc)}]   
        return lista_facturas
    
    def get_cascos(self):
        """
          Devuelve la cantidad de cascos que tiene un cliente en fabrica. Para el cierre de comercial, actualizar el saldo
        """
        cantidad = 0
        if self.externo==False:
            resultado1 = query_to_dicts("""
             SELECT 
                  count(casco_casco.casco_nro) as cantidad
                FROM 
                  public.casco_casco
                inner join public.casco_detallerc on casco_detallerc.casco_id = casco_casco.id_casco 
                inner join public.casco_recepcioncliente on casco_detallerc.rc_id = casco_recepcioncliente.doc_recepcioncliente_id 
                WHERE 
                  casco_casco.estado_actual NOT IN ('DC','ECR','Factura','DCC') AND 
                  casco_recepcioncliente.cliente_id = '"""+self.id+"""'""")
        else:
            resultado1 = query_to_dicts("""
             SELECT 
                  count(casco_casco.casco_nro) as cantidad
                FROM 
                  public.casco_casco
                inner join public.casco_detallerce on casco_detallerce.casco_id = casco_casco.id_casco 
                inner join public.casco_recepcascoext on casco_detallerce.recepcascoext_id = casco_recepcascoext.doc_recepcascoext_id
                WHERE 
                  casco_casco.estado_actual NOT IN ('DC','ECR','Factura','DCC') AND 
                  casco_recepcascoext.cliente_id = '"""+self.id+"""'""")
        for datos in resultado1:
            cantidad=datos['cantidad']
        return cantidad
    
class Contrato(models.Model):
    id_contrato=models.CharField(max_length=40, primary_key=True, unique=True)
    contrato_nro=models.CharField('Nro. contrato',max_length=10, unique=True)
#    cliente=models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha_vigencia=models.DateField('Fecha')
#    tiempo_vigencia=models.IntegerField(default=0)
    fecha_vencimiento=models.DateField('Fecha de vencimiento', null=True, blank=True)
    sucursal_mn=models.ForeignKey(Sucursales,related_name = 'SucursalMN',verbose_name='Sucursal CUP',on_delete=models.PROTECT, null=True, blank=True)
    cuenta_mn=models.CharField('Cuenta CUP',max_length=19, null=True, blank=True)
    titular_mn=models.CharField('Titular CUP',max_length=80, null=True, blank=True)
    
    sucursal_usd=models.ForeignKey(Sucursales,related_name = 'SucursalUSD',verbose_name='Sucursal CUC',on_delete=models.PROTECT, null=True, blank=True)
    cuenta_usd=models.CharField('Cuenta CUC',max_length=19, null=True, blank=True)
    titular_usd=models.CharField('Titular CUC',max_length=80, null=True, blank=True)
#    plan_contratado=models.PositiveIntegerField('Plan Contratado')
    cerrado=models.BooleanField(default=False)
    
    preciomn=models.BooleanField(default=False)
    preciocostomn=models.BooleanField(default=False)
    preciocuc=models.BooleanField(default=False)
    preciocostocuc=models.BooleanField(default=False)
    para_la_venta=models.BooleanField(default=False)
    tiempo_vigencia=models.IntegerField(default=0)
    precioextcup=models.BooleanField(default=False)
    otro_precio_casco=models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.contrato_nro
    class Meta:
        permissions = (("contrato","contrato"),)
        
    def get_plan_contratado(self,ano):
        objeto=Planes.objects.filter(contrato=self.id_contrato,plan_ano=ano)  
        plan_contratado=0
        for objects in objeto:
            plan_contratado=objects.plan_contratado
        return plan_contratado
    
    def get_plan_contratadoactual(self):
        from comerciax.casco.models import Fechacierre
        objeto=Planes.objects.filter(contrato=self.id_contrato,plan_ano=Fechacierre.objects.get(almacen='cm').year)  
        plan_contratado=0
        for objects in objeto:
            plan_contratado=objects.plan_contratado
        return plan_contratado
              

class ClienteContrato(models.Model):
    id_contratocliente=models.CharField(max_length=40, primary_key=True, unique=True)
    contrato=models.ForeignKey(Contrato, on_delete=models.PROTECT)
    cliente=models.ForeignKey(Cliente, on_delete=models.PROTECT)
    cerrado=models.BooleanField(default=False)
    
class ConsOrg(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    org=models.ForeignKey(Organismo,on_delete=models.PROTECT)
    class Meta:
        permissions = (("consorg","consorg"),)
       
class Area(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=25, unique=True)
    def __unicode__(self):
        return self.descripcion
    class Meta:
        ordering = ['descripcion']
        permissions = (("area","area"),)
    
class CausasRechazo(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=250,unique=True)
    def __unicode__(self):
        return self.descripcion
    class Meta:
        ordering = ['descripcion']
        permissions = (("causarechazo","causarechazo"),)
           
class Umedida(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=5,unique=True)
    def __unicode__(self):
        return self.descripcion
    class Meta:
        ordering = ['descripcion']
        permissions = (("umedida","umedida"),)

class ProductoManager(models.Manager):
    def get_by_natural_key(self,id,descripcion):
        return self.get(id=id,descripcion=descripcion)
    
class Producto(models.Model):
    objects = ProductoManager()
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=35, unique=True)
    precio_mn=models.DecimalField(max_digits=7, decimal_places=2)
    precio_costo_mn=models.DecimalField(max_digits=7, decimal_places=2)
    precio_cuc=models.DecimalField(max_digits=7, decimal_places=2)
    precio_costo_cuc=models.DecimalField(max_digits=7, decimal_places=2)
    um=models.ForeignKey(Umedida,on_delete=models.PROTECT)
    codigo=models.CharField(max_length=18, unique=True)
    precio_particular=models.DecimalField(max_digits=7, decimal_places=2)
    precio_casco=models.DecimalField(max_digits=7, decimal_places=2,default=0)
    precio_externo_cup=models.DecimalField(max_digits=7, decimal_places=2)
    precio_vulca=models.DecimalField(max_digits=7, decimal_places=2)
    otro_precio_casco=models.DecimalField(max_digits=7, decimal_places=2,default=0)
    precio_regrabable=models.DecimalField(max_digits=7, decimal_places=2,default=0)

    def natural_key(self):
        return (self.id,self.descripcion)
    def __unicode__(self):
        return self.descripcion
    class Meta:
        ordering = ['descripcion']
        unique_together = (('id', 'descripcion'),)
        permissions = (("producto","producto"),)
    
class Transpotador(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    contrato=models.ForeignKey(Contrato,on_delete=models.CASCADE)
    nombre=models.CharField(max_length=35)
    #licencia=models.CharField(max_length=10)
    ci=models.CharField(max_length=11)
    activo=models.BooleanField(default=True)
    def __unicode__(self):
        return self.nombre

    class Meta:
        unique_together = [("contrato", "ci")]
        permissions = (("transportador","transportador"),)
    
class Representante(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    contrato=models.ForeignKey(Contrato,on_delete=models.CASCADE)
    nombre=models.CharField(max_length=35)
    cargo=models.CharField('Cargo',max_length=35)
    ci=models.CharField(max_length=11, null=True, blank=True)
    nombramiento=models.CharField(max_length=10, null=True, blank=True)
    activo=models.BooleanField(default=True)
    def __unicode__(self):
        return self.nombre
    class Meta:
        unique_together = [("contrato", "ci")]
        permissions = (("representante","representante"),)

class FormasPago(models.Model): 
    id= models.CharField(max_length=40, primary_key=True, unique=True)  
    descripcion=models.CharField(max_length=25,unique=True)
    def __unicode__(self):
        return self.descripcion
    class Meta:
        permissions = (("formapago","formapago"),)

class Monedas(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=10,unique=True)
    def __unicode__(self):
        return self.descripcion
    class Meta:
        permissions = (("monedas","monedas"),)

class Empresa(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    provincia=models.ForeignKey(Provincias,verbose_name = 'Provincia',on_delete=models.PROTECT)
    codigo=models.CharField('C&oacute;digo Empresa',max_length=14) # Organismo.Subordinacion.CodigoEmpresa ---.-.-------- 
    nombre=models.CharField('Nombre de la Empresa',max_length=50)
    direccion=models.TextField('Direcci&oacute;n',max_length=200)
    fax=models.CharField('Fax',max_length=50, null=True, blank=True)
    email=models.EmailField('E-mail', null=True, blank=True)
    telefono=models.CharField('Tel&eacute;fono',max_length=50, null=True, blank=True)
    titular_usd=models.CharField('Titular CUC', max_length=35, null=True, blank=True)
    titular_mn=models.CharField('Titular CUP', max_length=35, null=True, blank=True)
    sucursal_mn=models.ForeignKey(Sucursales,related_name = 'SucursalEMN',verbose_name='Sucursal CUP',on_delete=models.PROTECT, null=True, blank=True)
    sucursal_usd=models.ForeignKey(Sucursales,related_name = 'SucursalEUSD',verbose_name='Sucursal CUC',on_delete=models.PROTECT, null=True, blank=True)
    cuenta_mn=models.CharField('Cuenta CUP',max_length=19, null=True, blank=True)
    cuenta_usd=models.CharField('Cuenta CUC',max_length=19, null=True, blank=True)
    
    class Meta:
        permissions = (("empresa","empresa"),)
        
class Planes(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    contrato=models.ForeignKey(Contrato, on_delete=models.CASCADE)
    plan_contratado=models.IntegerField(default=0)
    plan_ano=models.IntegerField(default=0)
    plan_enero=models.IntegerField(default=0)
    plan_febrero=models.IntegerField(default=0)
    plan_marzo=models.IntegerField(default=0)
    plan_abril=models.IntegerField(default=0)
    plan_mayo=models.IntegerField(default=0)
    plan_junio=models.IntegerField(default=0)
    plan_julio=models.IntegerField(default=0)
    plan_agosto=models.IntegerField(default=0)
    plan_septiembre=models.IntegerField(default=0)
    plan_octubre=models.IntegerField(default=0)
    plan_noviembre=models.IntegerField(default=0)
    plan_diciembre=models.IntegerField(default=0)
    
    
    def __unicode__(self):
        return self.plan_total
    class Meta:
        ordering = ['plan_ano']
        permissions = (("planes","planes"),)
        
        
class Fecha_Ver(models.Model):
    id = models.CharField(max_length=40, primary_key=True, unique=True)
    fecha=models.DateField()
    
    def __unicode__(self):
        return self.fecha
    class Meta:
        permissions = (("fecha_ver","fecha_ver"),) 
        
class Config_SMTPEmail(models.Model):
    servidor = models.CharField(max_length=250)
    puerto = models.IntegerField(default=0)
    ssl = models.BooleanField(default=False)
    correo = models.CharField(max_length=250)
    contrasena = models.CharField(max_length=128)
    
    def set_password(self, raw_password):
        self.contrasena = base64.b64encode(raw_password)
#        base64.b64decode(raw_password) para decodificar

class Servicio(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=50, unique=True)
    codigo = models.CharField(max_length=18, unique=True)
    um = models.ForeignKey(Umedida, on_delete=models.PROTECT)
    precio_mn=models.DecimalField(max_digits=18, decimal_places=2)
    activo = models.BooleanField(default=1)

    def __unicode__(self):
        return self.descripcion

    class Meta:
        ordering = ['descripcion']
        unique_together = (('id', 'descripcion'),)
        permissions = (("servicio","servicio"),)


class ProdAlter(models.Model):
    id=models.CharField(max_length=40, primary_key=True, unique=True)
    descripcion=models.CharField(max_length=50, unique=True)
    codigo = models.CharField(max_length=18, unique=True)
    um = models.ForeignKey(Umedida, on_delete=models.PROTECT)
    precio_mn=models.DecimalField(max_digits=18, decimal_places=2)
    activo = models.BooleanField(default=1)

    def __unicode__(self):
        return self.descripcion

    class Meta:
        ordering = ['descripcion']
        # unique_together = (('id', 'descripcion'),)
        permissions = (("producciones","producciones"),)
    
              