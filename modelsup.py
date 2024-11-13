from sqlalchemy import Column, Integer, Boolean, String, Date, Float, ForeignKey, TIMESTAMP, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Document(Base):
    __tablename__ = "Document"
    id_doc = Column(Integer, primary_key=True)
    seria = Column(Integer, nullable=False)
    nomer = Column(Integer, nullable=False)
    kem_vidan = Column(String(50))
    date_vidachi = Column(Date)

class NalichieSemui(Base):
    __tablename__ = "Nalichie_semui"
    id_nalichie = Column(Integer, primary_key=True)
    nalichie = Column(String(50))

class SostoyanieZdoroviya(Base):
    __tablename__ = "Sostoyanie_zdoroviya"
    id_sostoyanie = Column(Integer, primary_key=True)
    sostoyanie_zdoroviya = Column(String(50))

class Dolzenost(Base):
    __tablename__ = "Dolzenost"
    id_dolzenost = Column(Integer, primary_key=True)
    dolzenost = Column(String(50))

class Oborudovanie(Base):
    __tablename__ = "Oborudovanie"
    id_oborudovanie = Column(Integer, primary_key=True)
    oborud = Column(String(50))

class Dostup(Base):
    __tablename__ = "Dostup"
    id_dostup = Column(Integer, primary_key=True)
    FIO = Column(String(100))
    uroven_dostupa = Column(Integer, nullable=False)
    FK_oborudovanie = Column(Integer, ForeignKey("Oborudovanie.id_oborudovanie"))
    oborudovanie = relationship("Oborudovanie")

class Sotrudniki(Base):
    __tablename__ = "Sotrudniki"
    id_sotrudnika = Column(Integer, primary_key=True)
    FIO = Column(String(100))
    date_rozdenia = Column(Date)
    bank_rekviz = Column(Integer, nullable=False)
    FK_doument = Column(Integer, ForeignKey("Document.id_doc"))
    FK_nalichie_semui = Column(Integer, ForeignKey("Nalichie_semui.id_nalichie"))
    FK_sostoyanie_zdoroviya = Column(Integer, ForeignKey("Sostoyanie_zdoroviya.id_sostoyanie"))
    FK_dolzenost = Column(Integer, ForeignKey("Dolzenost.id_dolzenost"))
    FK_Dostup = Column(Integer, ForeignKey("Dostup.id_dostup"))

    document = relationship("Document")
    nalichie_semui = relationship("NalichieSemui")
    sostoyanie_zdoroviya = relationship("SostoyanieZdoroviya")
    dolzenost = relationship("Dolzenost")
    dostup = relationship("Dostup")

class MestaProd(Base):
    __tablename__ = "Mesta_prod"
    id_mesta = Column(Integer, primary_key=True)
    gorod = Column(String(50))

class TypeCompany(Base):
  __tablename__ = 'typecompany'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  name = Column(String(255), nullable=False)

class Partners(Base):
  __tablename__ = 'partners'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  type_partner = Column(Integer, ForeignKey('typecompany.id'))
  company_name = Column(String(255), nullable=False)
  ur_adress = Column(String(255), nullable=False)
  inn = Column(String(50), nullable=False)
  director_name = Column(String(255), nullable=False)
  phone = Column(String(50), nullable=False)
  email = Column(String(255), nullable=False)
  rating = Column(Integer, nullable=True)
  type_company = relationship("TypeCompany")

class ProductType(Base):
  __tablename__ = 'producttype'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  name = Column(String(255), nullable=False)
  coefficient = Column(Float, nullable=False)

class Product(Base):
  __tablename__ = 'product'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  type = Column(Integer, ForeignKey('producttype.id'))
  description = Column(String(255), nullable=False)
  article = Column(Integer, nullable=False)
  price = Column(Float, nullable=False)
  size = Column(Float, nullable=False)
  class_ = Column(Integer, nullable=False, name="class")  # 'class' - зарезервированное слово, используем 'class_'
  product_type = relationship("ProductType")

class PartnerProduct(Base):
  __tablename__ = 'partnerproduct'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  id_product = Column(Integer, ForeignKey('product.id'))
  id_partner = Column(Integer, ForeignKey('partners.id'))
  quantity = Column(Integer, nullable=False)
  date_of_sale = Column(Date, nullable=False)
  product = relationship("Product")
  partner = relationship("Partners")

class Material(Base):
  __tablename__ = 'material'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  name = Column(String(255), nullable=False)
  defect = Column(Float, nullable=True)

class MaterialProduct(Base):
  __tablename__ = 'materialproduct'
  id = Column(Integer, primary_key=True, autoincrement=True)  # автоинкремент
  id_product = Column(Integer, ForeignKey('product.id'))
  id_material = Column(Integer, ForeignKey('material.id'))
  product = relationship("Product")
  material = relationship("Material")

class TipMateriala(Base):
    __tablename__ = "Tip_materiala"
    id_materiala = Column(Integer, primary_key=True)
    tip_materiala = Column(String(50))
    procent_braka = Column(Float)

class Postavschiki(Base):
    __tablename__ = "Postavschiki"
    id_postavschika = Column(Integer, primary_key=True)
    tip_postavschika = Column(String(50))
    naimenovanie = Column(String(50))
    INN = Column(Integer, nullable=False)

class Materiali(Base):
    __tablename__ = "Materiali"
    id_materiala = Column(Integer, primary_key=True)
    FK_tip_materiala = Column(Integer, ForeignKey("Tip_materiala.id_materiala"))
    naimenovanie = Column(String(50))
    FK_postavschik = Column(Integer, ForeignKey("Postavschiki.id_postavschika"))
    kolichestvo_v_upakovke = Column(Integer, nullable=False)
    ed_izmereniya = Column(String(50))
    opisanie = Column(String(50))
    stoimost = Column(Integer, nullable=False)
    kolichestvo_na_sklade = Column(Integer, nullable=False)
    min_kolichestvo = Column(Integer, nullable=False)

    tip_materiala = relationship("TipMateriala")
    postavschik = relationship("Postavschiki")

class TipProdukcii(Base):
    __tablename__ = "Tip_produkcii"
    id_produkcii = Column(Integer, primary_key=True)
    tip_produkcii = Column(String(50))
    koeficient_tipa_prod = Column(Float)

class RazmerUpakovki(Base):
    __tablename__ = "Razmer_upakovki"
    id_razmera = Column(Integer, primary_key=True)
    dlina = Column(Integer, nullable=False)
    shirina = Column(Integer, nullable=False)
    visota = Column(Integer, nullable=False)

class Produkcia(Base):
    __tablename__ = "Produkcia"
    id_articul = Column(Integer, primary_key=True)
    Fk_tip_produkcii = Column(Integer, ForeignKey("Tip_produkcii.id_produkcii"))
    naimenovanie = Column(String(50))
    opisanie = Column(String(50))
    min_st = Column(Integer, nullable=False)
    FK_razmer_up = Column(Integer, ForeignKey("Razmer_upakovki.id_razmera"))
    ves_bez_up = Column(Integer, nullable=False)
    ves_s_up = Column(Integer, nullable=False)
    sertifikat = Column(Boolean)
    nomer_standarta = Column(Integer, nullable=False)
    kolichestvo = Column(Integer, nullable=False)
    vremya_izgotovleniya = Column(Date)
    sebestoimost = Column(Integer, nullable=False)
    nomer_zceha = Column(Integer, nullable=False)
    kolichestvo_chelovek = Column(Integer, nullable=False)
    FK_materiali_dlya_proizvodstva = Column(Integer, ForeignKey("Materiali.id_materiala"))

    tip_produkcii = relationship("TipProdukcii")
    razmer_upakovki = relationship("RazmerUpakovki")
    materiali_dlya_proizvodstva = relationship("Materiali")
   
class RealizazciyaProducta(Base):
    __tablename__ = "Realizazciya_producta"
    id_realizacii = Column(Integer, primary_key=True)
    fk_partner = Column(Integer, ForeignKey("partners.id"))
    fk_produkciya = Column(Integer, ForeignKey("Produkcia.id_articul"))
    summa = Column(Float, nullable=False)

    partner = relationship("Partners")
    produkciya = relationship("Produkcia")
   
class Connect:
    @staticmethod
    def create_session():
        engine = create_engine("postgresql://postgres:1@localhost:5433/postgres")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        return session