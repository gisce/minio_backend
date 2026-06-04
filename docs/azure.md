# Configuració dels mòduls Azure

Aquest document descriu què ha de preparar Infra a Azure Blob Storage i quines dades necessita l'equip d'aplicació per configurar els mòduls `azure_backend` i `ir_attachment_azure`.

## Abast

Els mòduls Azure d'aquest repositori permeten guardar binaris de l'ERP en Azure Blob Storage:

- `azure_backend`: defineix el camp `AzureBlobFile`, que desa i llegeix fitxers en contenidors d'Azure Blob Storage.
- `ir_attachment_azure`: substitueix el camp binari `datas` d'`ir.attachment` per `datas_azure`, de manera que els adjunts es desen a Azure i a la base de dades queda la ruta del blob.

## Funcionament de l'aplicació

- L'aplicació crea un client d'Azure segons el valor de `azure_auth_mode`.
- Si no s'informa `azure_auth_mode`, s'usa `connection_string` per compatibilitat amb la configuració existent.
- Quan s'escriu un fitxer, el mòdul puja un `BlockBlob` al contenidor configurat i desa a la base de dades la ruta del blob.
- Quan es llegeix un fitxer, el mòdul descarrega el blob i retorna el contingut en base64.
- Quan s'esborra un fitxer o un adjunt, el mòdul elimina el blob corresponent.
- Si el contenidor no existeix, el codi intenta crear-lo automàticament.

El patró de ruta dels objectes és:

```text
<taula>/<id>_<nom_camp_o_fitxer>
<taula>/<subcarpeta>/<id>_<nom_camp_o_fitxer>
```

Per `ir_attachment_azure`, el contenidor per defecte és `attachments` i la subcarpeta acostuma a ser el model relacionat de l'adjunt.

## Procediment per Infra

1. Crear o reutilitzar un Resource Group i una subscripció Azure per l'entorn corresponent.
2. Crear un Storage Account per a Blob Storage. Recomanat:
   - tipus `StorageV2` o equivalent actual per Blob Storage general,
   - rendiment `Standard`, excepte si hi ha un requisit explícit de latència o throughput,
   - access tier `Hot` per adjunts consultables habitualment,
   - accés anònim desactivat,
   - connexions HTTPS obligatòries.
3. Definir la redundància segons criticitat i RPO/RTO:
   - `LRS` per entorns no crítics o cost més baix,
   - `ZRS` si cal tolerància dins la regió,
   - `GRS` o `GZRS` si cal recuperació davant caiguda regional.
4. Configurar xarxa:
   - si l'ERP s'executa a Azure o en una xarxa connectada, prioritzar Private Endpoint i DNS privat,
   - si l'ERP surt per Internet, limitar l'accés públic als IPs de sortida de l'ERP,
   - evitar deixar el Storage Account obert a totes les xarxes en producció.
5. Crear els contenidors necessaris:
   - `attachments`, si s'usa `ir_attachment_azure` sense sobreescriure configuració,
   - qualsevol altre contenidor que s'hagi definit en camps `AzureBlobFile('...', '<container>')`.
6. Configurar els contenidors amb nivell d'accés privat. No cal exposar URLs públiques per al funcionament del mòdul.
7. Escollir el mode d'autenticació i proporcionar les credencials corresponents:
   - `connection_string`: connection string del Storage Account.
   - `sas_token`: URL del Blob Service amb SAS token amb permisos suficients.
   - `app_registration`: App Registration d'Azure AD amb permisos RBAC sobre el Storage Account.
8. Garantir que el mode escollit permet lectura, escriptura i esborrat de blobs. Si els contenidors no es precreen, també ha de permetre crear-los.
9. Desar credencials, SAS tokens o secrets d'App Registration en un gestor de secrets o en el mecanisme segur de configuració de l'entorn. No s'han de versionar en cap repositori.
10. Definir protecció de dades:
   - habilitar soft delete de blobs i contenidors si cal capacitat de recuperació,
   - valorar blob versioning segons política de retenció,
   - definir lifecycle management si cal moure dades antigues a tiers més econòmics o expirar-les.
11. Activar monitoratge:
    - diagnostic logs del Storage Account,
    - mètriques de disponibilitat, latència, errors i capacitat,
    - alertes per errors 4xx/5xx, throttling, creixement inesperat i expiració/rotació de claus.
12. Documentar el pla de rotació. Segons el mode, caldrà actualitzar la connection string, regenerar el SAS token o rotar el secret de l'App Registration i reiniciar o recarregar el servei segons el mecanisme de configuració.

## Normes de nomenclatura

- El nom del Storage Account ha de ser únic dins d'Azure, entre 3 i 24 caràcters, amb lletres minúscules i números.
- El nom del contenidor ha de tenir entre 3 i 63 caràcters, en minúscules, amb lletres, números i guions. Ha de començar i acabar amb lletra o número.
- El codi aplica `slugify` al nom del contenidor definit al camp `AzureBlobFile`, per tant cal coordinar el nom final si conté accents, espais o majúscules.

## Dades que necessitem per configurar l'ERP

| Dada | Obligatori | Descripció |
| --- | --- | --- |
| Entorn | Sí | `dev`, `test`, `pre`, `prod` o el nom intern de l'entorn. |
| `azure_auth_mode` | No | Mode d'autenticació. Valors suportats: `connection_string`, `sas_token`, `app_registration`. Si no s'informa, s'usa `connection_string`. |
| `azure_connection_string` | Sí en `connection_string` i `sas_token` | En mode `connection_string`, connection string del Storage Account. En mode `sas_token`, URL del Blob Service amb SAS token. |
| `azure_connection_tenant_id` | Sí en `app_registration` | Tenant ID d'Azure AD. |
| `azure_connection_client_id` | Sí en `app_registration` | Client ID de l'App Registration. |
| `azure_connection_client_secret` | Sí en `app_registration` | Secret de l'App Registration. |
| `azure_connection_account_url` | Sí en `app_registration` | URL del Blob Service, per exemple `https://<storage-account>.blob.core.windows.net`. |
| `azure_bucket_attachment` | No | Nom del contenidor per `ir_attachment_azure`. Si no s'informa, s'usa `attachments`. |
| Storage Account | Sí | Nom del Storage Account per identificar l'actiu i coordinar suport. |
| Resource Group i subscripció | Sí | Ubicació administrativa del recurs Azure. |
| Regió Azure | Sí | Regió on s'ha desplegat el Storage Account. |
| Contenidors creats | Sí | Llista de contenidors disponibles i quin mòdul o camp els utilitza. |
| Configuració de xarxa | Sí | Private Endpoint, DNS privat, IPs permesos o regla de firewall aplicable. |
| Política de retenció | Recomanat | Soft delete, versioning, backup i lifecycle configurats. |
| Contacte d'Infra | Recomanat | Equip o persona responsable del Storage Account i de la rotació de claus. |

En entorns on la configuració es passa per variables d'entorn, les claus esperades segueixen la convenció de l'ERP:

```text
OPENERP_AZURE_AUTH_MODE=connection_string
OPENERP_AZURE_CONNECTION_STRING=<connection-string>
OPENERP_AZURE_BUCKET_ATTACHMENT=attachments
```

En fitxer de configuració, les claus són:

```ini
azure_auth_mode = connection_string
azure_connection_string = <connection-string>
azure_bucket_attachment = attachments
```

Per mode SAS:

```text
OPENERP_AZURE_AUTH_MODE=sas_token
OPENERP_AZURE_CONNECTION_STRING=https://<storage-account>.blob.core.windows.net?<sas-token>
```

```ini
azure_auth_mode = sas_token
azure_connection_string = https://<storage-account>.blob.core.windows.net?<sas-token>
```

Per mode App Registration:

```text
OPENERP_AZURE_AUTH_MODE=app_registration
OPENERP_AZURE_CONNECTION_TENANT_ID=<tenant-id>
OPENERP_AZURE_CONNECTION_CLIENT_ID=<client-id>
OPENERP_AZURE_CONNECTION_CLIENT_SECRET=<client-secret>
OPENERP_AZURE_CONNECTION_ACCOUNT_URL=https://<storage-account>.blob.core.windows.net
```

```ini
azure_auth_mode = app_registration
azure_connection_tenant_id = <tenant-id>
azure_connection_client_id = <client-id>
azure_connection_client_secret = <client-secret>
azure_connection_account_url = https://<storage-account>.blob.core.windows.net
```

## Exemple local amb Azurite

Els tests usen Azurite com a emulador de Blob Storage. Un exemple de connection string local és:

```text
DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=password;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
```

Aquest exemple només és per desenvolupament o CI. En entorns reals s'ha d'usar HTTPS i una connection string del Storage Account productiu o de l'entorn corresponent.

## Validacions abans de passar a producció

- L'ERP arrenca sense l'error `Missing Azure Blob Storage configuration`.
- El mòdul `azure_backend` està instal·lat abans que qualsevol mòdul que declari camps `AzureBlobFile`.
- Si s'usen adjunts, `ir_attachment_azure` està instal·lat i el contenidor configurat existeix o pot ser creat pel servei.
- Es pot crear un adjunt i verificar que apareix un blob amb patró `ir_attachment/<id>_<fitxer>`.
- Es pot llegir l'adjunt des de l'ERP després de pujar-lo.
- Es pot modificar l'adjunt i comprovar que el blob antic s'elimina quan canvia el nom.
- Es pot esborrar l'adjunt i comprovar que el blob desapareix o queda en estat recuperable si soft delete està habilitat.
- Els backups de base de dades i blobs estan coordinats: la base de dades conté la ruta del blob, però no el contingut binari.

## Limitacions actuals

- El mòdul suporta `connection_string`, `sas_token` i `app_registration`; no suporta Managed Identity.
- El mode `connection_string` amb clau de compte dona accés ampli al Storage Account. Cal compensar-ho amb secret management, firewall, Private Endpoint i rotació de claus.
- El mode `sas_token` redueix l'abast de la credencial, però exigeix gestionar-ne caducitat, permisos i rotació.
- El mode `app_registration` evita claus de compte i SAS tokens, però requereix RBAC correcte sobre el Storage Account i rotació del `client_secret`.
- El codi intenta crear contenidors automàticament. Si Infra vol que els contenidors siguin 100% governats per IaC, s'han de precrear i validar permisos abans de desplegar.
- Si un blob s'esborra manualment a Azure però la base de dades conserva la ruta, la lectura pot fallar.
- Els fitxers es processen en memòria com a base64. Cal validar límits funcionals si es preveuen adjunts grans.

## Referències

- Azure Blob Storage: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction
- Connection strings d'Azure Storage: https://learn.microsoft.com/en-us/azure/storage/common/storage-configure-connection-string
- Regles de nom de Storage Account: https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview
- Regles de nom de contenidors i blobs: https://learn.microsoft.com/en-us/rest/api/storageservices/Naming-and-Referencing-Containers--Blobs--and-Metadata
- Firewalls i xarxa d'Azure Storage: https://learn.microsoft.com/en-us/azure/storage/common/storage-network-security
- Soft delete i protecció de dades: https://learn.microsoft.com/en-us/azure/storage/blobs/soft-delete-blob-overview
- Lifecycle management: https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-overview
