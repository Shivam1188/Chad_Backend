import pandas as pd
import re

# Raw data (copy-paste your text here as a multi-line string)
raw_data = """
Abseits
Kleiner Schlossplatz 13/15, 70173 Stuttgart
+49 711 621451
abseitsgermany.com
View on map
APRIL FIRST
Auguststrasse 77, 10117 Berlin
+49 30 65219144
aprilfirst.de
View on map
Basler Beauty - Online Only
Germany
basler-beauty.de
View on map
Beauties Lab - Online Only
10 Avenue Laurier O, Montreal, Canada, H2T 2N3
beautieslab.co/en-us
View on map
BEBE Concept
Trenow 55, 05-080 (Laski), Poland
+48 511 687 519
ebebeconcept.de
View on map
big. Beauty
219 Victoria Park Rd, London E9 7HD
07852 851236
big-beauty.co.uk
View on map
Blanda Beauty
Wörthstr. 17
Reutlingen, 72764
Germany
blanda-beauty.com
View on map
BLOS
DOKTER WILLEMSSTRAAT 16
Hasselt, 3500
Belgium
blos-shop.com
View on map
Bluemercury - Brentwood
11640 San Vicente Blvd. Los Angeles, CA
(310) 442-5900
bluemercury.com
View on map
Bluemercury - Buckhead
37 West Paces Ferry Road. Atlanta, GA 30305
(404) 467-9100
bluemercury.com
View on map
Bluemercury - Chesterbrook
6230 Old Dominion Drive
(703) 782-9899
bluemercury.com
View on map
Bluemercury - Chestnut St
2060 Chestnut Street San Francisco, CA 94123
(415) 346-3460
bluemercury.com
View on map
Bluemercury - Chicago (River North)
356 N Clark St, Chicago, IL 60654
(312) 595-9599
bluemercury.com
View on map
Bluemercury - Chicago (State & Elm)
1153 N State St, Chicago, IL 60610
(312) 397-0063
bluemercury.com
View on map
Bluemercury - El Segundo
840 N Sepulveda Blvd b106, El Segundo, CA 90245
(310) 416-1006
bluemercury.com
View on map
Bluemercury - Fenton Market
1 Fenton Main St Suite 130, Cary, NC 27511
(984) 209-1777
bluemercury.com
View on map
Bluemercury - Georgetown
3059 M Street, NW. Washington DC 20007
(443) 824-4456
bluemercury.com
View on map
Bluemercury - La Jolla
7802 Girard Avenue. La Jolla. CA 92037
(858) 456-3870
bluemercury.com
View on map
Bluemercury - Lincoln Park Chicago
2208 North Halsted. Chicago IL 60614
(773) 327-6900
bluemercury.com
View on map
Bluemercury - Miramar Beach
500 Grand Blvd, Miramar Beach, FL 32550
(850) 650-2570
bluemercury.com
View on map
Bluemercury - New York (68th & 3rd)
1164 Third Avenue New York, NY 10065
(212) 988-1141
bluemercury.com
View on map
Bluemercury - New York (88th & 3rd)
1566 Third Ave. New York, NY
(646) 351-6701
bluemercury.com
View on map
Bluemercury - Newbury St
160 Newbury Street. Boston, MA 02116
(617) 424-0004
bluemercury.com
View on map
Bluemercury - Promenade at Sagemore
500 Route 73 S. Marlton NJ 8053
(856) 985-9226
bluemercury.com
View on map
Bluemercury - Rittenhouse Square
1707 Walnut St, Philadelphia, PA 19103
(215) 569-3100
bluemercury.com
View on map
Bluemercury - Westport 2
57 Main Street Westport, CT 06880
(203) 222-9222
bluemercury.com
View on map
Blush Portugal
Cascais, Avenida Saboia 935B, Portugal
blushportugal.com
View on map
Boutique Jole
Via Paolo Baratta 96/106, Battipaglia (SA) 84091
+39 0828 300168
jole.it
View on map
C.O. Bigelow
414 Sixth Avenue New York, NY 10011
(212) 533-2700
bigelowchemists.com
View on map
Chenot Palace
Hertensteinstrasse 34, 6353 Weggis, Switzerland
+41 41 255 21 60
chenot.com
View on map
Claridges Spa
Claridges, Brook St, London W1K 4HR
020 7409 6565
claridges.co.uk/spa
View on map
Clover Mill
Cradley, Malvern, Worcestershire WR13 5NR
01886 880859
theclovermill.com
View on map
Comptoir 102
102 Beach Road, Jumeirah 1, Dubai, United Arab Emirates
comptoir102.com
View on map
Cosmetica Armadale
1048 - 1050 High Street
Armadale VIC 3143
mecca.com/en-au
View on map
Cosmetica Burnside Village
Burnside Village, Ground Floor, Shop 20
447 Portrush Road
Glenside SA 5065
mecca.com/en-au
View on map
Cosmetica Canberra Centre
The Canberra Centre, Level 1, Shop AF25
Bunda Street
Canberra ACT 2601
mecca.com/en-au
View on map
Cosmetica Carlton
2/356 Lygon Street
Carlton VIC 3053
mecca.com/en-au
View on map
Cosmetica Claremont
Claremont Quarter, Level 1 Cnr St Quentin Ave &, Bay View Terrace
mecca.com/en-au
View on map
Cosmetica Pacific Fair
Pacific Fair Shopping Centre, Shop 2768
Hooker Boulevard
Pacific Fair QLD 4218
mecca.com/en-au
View on map
Cosmetica Queens Plaza
Queens Plaza, Ground Floor, Shop 21
226 Queen Street
Brisbane QLD 4000
mecca.com/en-au
View on map
Cosmetica Toorak Rd
79 Toorak Road
South Yarra VIC 3141
mecca.com/en-au
View on map
Cult Beauty - Online Only
London, UK
cultbeauty.co.uk
View on map
Drake Store
Rue des Alpes 13, 1201 Geneva, Switzerland
+41 22 732 36 86
drake-store-shop.ch/de
View on map
DU NORD (Oldenburg)
Heiligengeistwall 11, 26122 Oldenburg, Germany
du-nord.com
View on map
Duchess
641 Old Post Rd, Bedford, NY 10506
(914) 219-4225
shopatduchess.com
View on map
Farmacy Sofia
Filikis Eterias 9, 65403 Kavala, Greece
View on map
FOEGER MOSER
Obermarktstraße 20, 6410 Telfs, Tirol, Austria
foeger.com
View on map
Free People - 1835
4999 Old Orchard Ctr. Skokie IL, 60077
(847) 763-1624
freepeople.com
View on map
Free People - 1836
1102 NW Davis Street. Portland OR, 97209
(503) 227-2691
freepeople.com
View on map
Free People - 1847
2000 S. Blvd. Charlotte NC, 28203-5041
(704) 335-3414
freepeople.com
View on map
Free People - 1866
899 Boylston St. Boston MA, 02115
857-245-6156
freepeople.com
View on map
Free People - 1877
1214 First Street. Napa CA, 94559-2930
(707) 308-7475
freepeople.com
View on map
Free People - 1883
4771 E County Hwy 30A Unit C106, Santa Rosa Beach, FL 32459
(850) 397-1576
freepeople.com
View on map
Free People - 1885
13347 S Teal Ridge Way. Riverton UT, 84096
(385) 404-4249
freepeople.com
View on map
Free People - 1886
460 Orlando Ave. Winter Park FL, 32789-2935
(689) 223-4012
freepeople.com
View on map
Free People - 804
690 West Dekalb Pike. King of Prussia PA, 19406
(610) 354-8926
freepeople.com
View on map
Free People - 813
8687 North Central Expy., #2420. Dallas TX, 75225
(469) 232-2262
freepeople.com
View on map
Free People - 821
1181 Broadway Plaza St. Walnut Creek CA, 94596
(925) 932-1011
freepeople.com
View on map
Free People - 832
524 Lamar Blvd.. Austin TX, 78703
(512) 320-1950
freepeople.com
View on map
Free People - 835
7014 E. Camelback Road. Scottsdale AZ, 85251
(480) 945-1090
freepeople.com
View on map
Free People - 838
3000 E 1st Avenue. Denver CO, 80206
(303) 322-4676
freepeople.com
View on map
Free People - 842
1636 Redwood Highway. Corte Madera CA, 94925
(415) 924-8401
freepeople.com
View on map
Free People - 845
5135 W. Alabama Street. Houston TX, 77056
(713) 439-0307
freepeople.com
View on map
Free People - 848
1 East Joppa Road. Towson MD, 21286
(410) 296-7842
freepeople.com
View on map
goop Bond Street
25 Bond Street. New York City, NY 10012
(917) 261-7683
goop.com
View on map
goop Brentwood
225 26th Street, Suite 37. Santa Monica, CA 90402
(310) 260-4072
goop.com
View on map
goop Marin
2215 Larkspur Landing Circuit, Unit 25A, Larkspur, CA 94939
+1 415-785-3748
goop.com
View on map
goop Miramar
1759 South Jameson Lane. Montecito, CA 93108
(805) 324-4563
goop.com
View on map
goop Sag Harbor
4 Bay Street. Sag Harbor, NY 11963
(631) 808-3930
goop.com
View on map
Green Lane
Mühlegasse 21, 8001 Zürich, Switzerland
41442610235
greenlanebeauty.com
View on map
Hotel Chelsea
222 W 23rd St, New York, NY 10011
(212) 483-1010
hotelchelsea.com
View on map
Juist ANA
Wilhelmstraße 14, 26571 Juist, Germany
+49 4935 921922
juistana.de
View on map
Kirna Zabete - Bryn Mawr, PA
915 Lancaster Ave Suite 170, Bryn Mawr, PA 19010
(610) 581-7777
kirnazabete.com
View on map
Kirna Zabete - East Hampton, NY
66 Newton Lane, East Hampton, NY 11937
(631) 527-5794
kirnazabete.com
View on map
Kirna Zabete - Madison Ave, NY
943 Madison Ave, New York, NY 10021
(646) 410-0025
kirnazabete.com
View on map
Kirna Zabete - Nashville, TN
2001 Warfield Drive, Nashville, TN 37215
(615) 621-2081
kirnazabete.com
View on map
Kirna Zabete - Palm Beach, FL
340 Royal Poinciana Way, Suite 305, Palm beach, FL 33480
(561) 791-6075
kirnazabete.com
View on map
Kirna Zabete - Soho, NY
160 Mercer Street, New York, NY 10012
(212) 941-9656
kirnazabete.com
View on map
L'Absurde
50 High Street, Margate, England CT9 1DS
07910 478370
labsurde.co.uk
View on map
Le Pink & Co
3208 W Sunset Blvd, Los Angeles, CA 90026
(323) 661-7465
lepinkandco.com
View on map
Lemon Laine
1900 Eastland Ave. #102 Nashville, TN 37206
(629) 702-6940
lemonlaine.myshopify.com
View on map
Liberty
Regent St., Carnaby, London W1B 5AH
libertylondon.com
View on map
LODENFREY VERKAUFS
Maffeistraße 7, 80333 Munchen, Germany
+49 89 210390
lodenfrey.com
View on map
Mecca Bondi
Westfield Bondi Junction, Level 4, Shop 4047 500 Oxford St, Bondi Junction NSW 2022
mecca.com/en-au
View on map
Mecca Chadstone
Shop G-074 Chadstone Shopping Centre, 1341 Dandenong Road, Chadstone VIC 3148
mecca.com/en-au
View on map
Mecca Double Bay
Cosmopolitan Shopping Centre, Shop G18, 2-22 Knox Street, Double Bay NSW 2028
mecca.com/en-au
View on map
Mecca George St
45 Market St, Sydney NSW 2000
mecca.com/en-au
View on map
Mecca Highpoint
Shop L03 3100A, Highpoint Shopping Centre, 20-200 Rosamond Road, Maribyrnong VIC 3032
mecca.com/en-au
View on map
Mecca Karrinyup
Shop MJ1270A, 200 Karrinyup Road, Karrinyup WA 6018
mecca.com/en-au
View on map
Mecca Mosman
814 - 816 Military Road, Mosman NSW 2088
mecca.com/en-au
View on map
Mecca Myer Melbourne
Myer Melbourne, 295 Lonsdale Street, Melbourne VIC 3000
mecca.com/en-au
View on map
Mecca Newmarket
Shop S270, Westfield Newmarket, 242-248 Broadway, Newmarket, Auckland 1023
mecca.com/en-au
View on map
Mecca Northland
Shop J045 - Northland Shopping Centre, 2-50 Murray Road, Preston VIC 3072
mecca.com/en-au
View on map
Mecca Sorrento
57-59 Ocean Beach Road, Sorrento VIC 3943
mecca.com/en-au
View on map
Mecca Wellington
Shop 260 Lambton Quay, Lambton Quay 6011
mecca.com/en-au
View on map
Moda Operandi - Online Only
New York, US
modaoperandi.com
View on map
MODE LENK
Lammstraße 4, 75172 Pforzheim, Germany
modelenk.de
View on map
Monk Estate
11101 CA-1 #105, Point Reyes Station, CA 94956
(415) 420-7302
monkestate.com
View on map
Muse & Heroine - Online Only
Europe
museandheroine.com
View on map
Net-a-Porter - Online Only
London, UK
net-a-porter.com
View on map
Niche Beauty - Online Only
Hamburg, Germany
niche-beauty.com
View on map
North Glow - Online Only
Denmark
northglow.de
View on map
Now Wow
NEUBAUGASSE 65,
Wien, Wien 1070
Austria
nowwow.shop
View on map
Oh My Cream ! Abbesses
90 rue des Martyrs
Paris, Paris 75018
France
(+33) 1 42 59 22 14
en.ohmycream.com
View on map
Oh My Cream ! Bac
104 rue du Bac
Paris, Paris 75007
Paris
View on map
Oh My Cream ! Bordeaux
13 rue de Temple
Bordeaux, Bordeaux 33000
France
(+33)05 57 83 45 77
en.ohmycream.com
View on map
Oh My Cream ! Charonne
40 rue de Charonne
Paris, Paris 75011
France
(+33)01 47 00 33 79
View on map
Oh My Cream ! Debelleyme
17 rue Debelleyme
Paris, Paris 75003
France
(+33)01 56 06 91 30
en.ohmycream.com
View on map
Oh My Cream ! Francs-Bourgeois
48 rue des Francs Bourgeois
Paris, Paris 75003
France
+330140619376
en.ohmycream.com
View on map
Oh My Cream ! Guichard
2 rue Guichard
Paris, Paris 75016
France
(+33)01 45 04 59 32
en.ohmycream.com
View on map
Oh My Cream ! King's Road
194 King's Road
London, London SW3 5XP
United Kingdom
020 7352 4184
ohmycream.co.uk
View on map
Oh My Cream ! Legendre
67 rue Legendre
Paris, Paris 75017
France
+3301 42 63 17 75
en.ohmycream.com
View on map
Oh My Cream ! Lille
4 rue Bartholomé Masurel
Lille, Lille 59800
France
(+33)03 20 13 74 75
en.ohmycream.com
View on map
Oh My Cream ! Lyon
17 rue Emile Zola
Lyon, Lyon 69002
France
(+33) 9 67 33 28 79
en.ohmycream.com
View on map
Oh My Cream ! Marylebone
24 New Cavendish Street
London, London W1G 8TU
United Kingdom
020 7018 8808
ohmycream.co.uk
View on map
Oh My Cream ! Montmarte
78 rue Montmarte
Paris, Paris 75002
France
+3301 72 38 91 36
en.ohmycream.com
View on map
Oh My Cream ! Notting Hill
243 Westbourne Grove
London, London W11 2SE
United Kingdom
020 7792 3862
ohmycream.co.uk
View on map
Oh My Cream ! Parly 2
Center commercial Parly 2 - 2 Av. Charles de Gaulle
78150, Le Chesnay-Rocquencourt 78150
France
(+33)01 39 46 25 29
en.ohmycream.com
View on map
Oh My Cream ! St Honore
5 rue du Marché St Honoré
Paris, Paris 75001
France
(+33) 01 40 39 99 86
en.ohmycream.com
View on map
Oh My Cream ! Studio Saintonge
51 Rue de Saintonge
Paris, Paris 75003
France
+330172389135
en.ohmycream.com
View on map
Oh My Cream ! Vavin
17 rue Vavin
Paris, Paris 75006
France
+3301 42 49 79 43
en.ohmycream.com
View on map
Olivela - Online Only
New York, US
olivela.com
View on map
Revolve - Online Only
Los Angeles, US
revolve.com
View on map
Saks Fifth Avenue
611 Fifth Avenue. New York, NY, 10022
(212) 753-4000
saksfifthavenue.com
View on map
SANDRA BRUYNS
THIJSAKKERSTRAAT 21
Hoogstraten, 2320
Belgium
sandrabruyns.be
View on map
SCHNEEWEISS
Wollzeile 20 - 1010 Vienna, Austria
+43 1 9166416
thestorebyschneeweiss.com
View on map
Selfridges
400 Oxford Street, London, W1A 1AB
020 7160 6222
selfridges.com
View on map
She's Lost Control
74 Broadway Market, London E8 4QJ
020 3196 7690
sheslostcontrol.co.uk
View on map
Skins Amsterdam Negen Straatjes
Runstraat 11, 1016 GJ Amsterdam, Netherlands
+31 20 240 0199
skins.nl/en
View on map
Skins Conservatorium
Van Baerlestraat 27, 1071 AN Amsterdam
+31 (0)20 528 6176
skins.nl/en
View on map
Skins Gateway
Shop F098, Gateway Theatre of Shopping, 1 Palm Boulevard, Umhlanga Ridge, Newtown Centre, Umhlanga, 4319
+27 31 020 1001
skins.co.za
View on map
Skins Gent
Korenmarkt 16, 9000 Gent, Belgium
+32 9 298 04 73
skins.nl/en
View on map
Skins Hyde Park
Shop UM39, Hyde Park Corner Shopping Centre, Corner Jan Smuts Avenue and William Nicol Drive, 6th Road, Hyde Park
Johannesburg, 2196
+27 (87) 562 9990
skins.co.za
View on map
Skins Laren
Naarderstraat 17, 1251 AX Laren, Netherlands
+31 35 531 1890
skins.nl/en
View on map
Skins Mall of Africa
Shop 2004, Mall of Africa, Magwa Cresent, Midrand, 2066
+27 (10) 500 0704
skins.co.za
View on map
Skins Menlyn
Shop G58 & G58A, Lower Empire Street, Menlyn Park Shopping Centre, Atterbury Rd &, Lois Ave, Menlyn, Pretoria, 0063
+27 (12) 030 1125
skins.co.za
View on map
Skins Sandton City
Shop U79 Upper Level, Sandton City Shopping Center, Sandton, 2031
+27 (11) 883-1350
skins.co.za
View on map
Skins Victoria Wharf
Shop 6214 Upper Level, Victoria Wharf Shopping Centre, Cape Town, 8001
+27 (21) 065-0331
skins.co.za
View on map
Space 519
200 E Chestnut St, Chicago, IL 60611
(312) 751-1519
space519.com
View on map
Space NK - Arndale (Manchester)
Unit 8, Manchester Arndale, Market St, Manchester M4 3AJ
020 3931 8605
spacenk.com
View on map
Space NK - Battersea
Battersea Power Station, Turbine Hall, Battersea Power Station, Upper Ground, Circus Rd S, London SW11 8BZ
020 3941 2877
spacenk.com
View on map
Space NK - Blackheath
33-35 Tranquil Vale, Blackheath, London SE3 0BU
020 3931 8603
spacenk.com
View on map
Space NK - Brighton
6 Bartholomews, Brighton, BN1 1HG
01273 776774
spacenk.com
View on map
Space NK - Canary Wharf
Cabot Place East, Canary Wharf, London, E14 4QS
020 7719 1902
spacenk.com
View on map
Space NK - Cardiff
Unit LG 68, St Davids Shopping Centre, The Hayes, St Davids Centre, Cardiff CF10 1GA
020 3941 2869
spacenk.com
View on map
Space NK - Cheapside
145-147 Cheapside, London EC2V 6BJ
020 3931 8624
spacenk.com
View on map
Space NK - Cobham
9 Oakdene Parade, Cobham, KT11 2LR
01932 860676
spacenk.com
View on map
Space NK - Donegall Square (Belfast)
5-6 Donegall Square N, Belfast BT1 5GB
028 9033 0833
spacenk.com
View on map
Space NK - Duke of York (Chelsea)
27 Duke of York Square, London, SW3 4LY
020 7730 9841
spacenk.com
View on map
Space NK - Exeter
Shopping Centre, 28 Princesshay, Exeter EX1 1GE
0300 124 8282
spacenk.com
View on map
Space NK - Glasgow
36-37 48 Princes Square, Buchanan St, Glasgow G1 3BZ
0141 248 7931
spacenk.com
View on map
Space NK - Grafton Street
82 Grafton Street, Centre, Dublin 2, D02 EV88, Ireland
+353 1 677 8615
spacenk.com
View on map
Space NK - Guildford
120 High St, Guildford GU1
Ê020 3931 8618
spacenk.com
View on map
Space NK - Hans Crescent (Knightsbridge)
40 Hans Crescent, London, SW1X 0LZ
020 7581 2518
spacenk.com
View on map
Space NK - Haslemere
31-33 High Street, Haslemere, GU27 2HG
01428 748681
spacenk.com
View on map
Space NK - Islington
299 Upper Street, London, N1 2TU
020 7704 2822
spacenk.com
View on map
Space NK - Kings Cross
2 Pancras Sq, London N1C 4AG
020 3976 4578
spacenk.com
View on map
Space NK - Leeds
19 Albion St, Leeds LS1 6HW
020 3931 8612
spacenk.com
View on map
Space NK - Loughton
291 High Road, Loughton, IG10 1AH
020 8508 3029
spacenk.com
View on map
Space NK - New Covent Garden
5 Neal Street, London, WC2H 9PU
020 3941 2859
spacenk.com
View on map
Space NK - Northcote Road
46 Northcote Road, London, SW11 1NZ
020 7228 7563
spacenk.com
View on map
Space NK - Parsons Green
205 New King's Road, London, SW6 4SR
020 7736 6728
spacenk.com
View on map
Space NK - Primrose Hill
156 Regent's Park Road, London, NW1 8XN
020 7586 9314
spacenk.com
View on map
Space NK - Regent Street
285-287 Margaret St, London W1B 2HH
020 3196 3541
spacenk.com
View on map
Space NK - Sevenoaks
98 High Street, Sevenoaks, TN13
020 3931 8600
spacenk.com
View on map
Space NK - St James Quarter (Edinburgh)
Unit 3.13b, St James Quarter, 310 Saint James Square, Edinburgh EH1 3AE
0300 124 8276
spacenk.com
View on map
Space NK - Tenterden
22 High St, Tenterden TN30 6AP
01580 854398
spacenk.com/uk/home
View on map
Space NK - Tunbridge Wells
41 High St, Tunbridge Wells TN1 1LX
020 3941 2855
spacenk.com
View on map
Space NK - Westfield White City
Unit SU1214, Westfield Shopping Centre, 2080 Ariel Way, London W12 7GD
020 3931 8640
spacenk.com
View on map
SSENSE - Online Only
Montreal, Canada
ssense.com/en-us
View on map
Studio Anatomy
1st Floor, 1 King Edward's Rd, London E9 7SF
View on map
The Dream Of
Studio 18, Hackney Downs Studios, London, United Kingdom E8 2BT
the-dream-of.com
View on map
The Emory
Old Barrack Yard, London SW1X 7NP
020 7862 5200
the-emory.co.uk
View on map
The Great Eros
135 Wythe Ave. Brooklyn, NY 11249
(718) 384-3767
thegreateros.com
View on map
The Standard Hotel
The Standard, 10 Argyle St, London WC1H 8EG
020 3981 8888
standardhotels.com/london
View on map
Venier Boutique
Via Della Mostra 23 39100 Bolzano, Italy
+39 0471 975540
View on map
Violet Grey
8452 Melrose Pl, Los Angeles, CA 90069
(323) 782-9700
violetgrey.com/en-us
View on map
Zapp - Online Only
United Kingdom
justzapp.com
"""  # Add all your data here
stores = raw_data.strip().split('View on map')

data_list = []

for store in stores:
    lines = [line.strip() for line in store.split('\n') if line.strip()]
    if not lines:
        continue
    
    store_name = lines[0]
    
    # Extract phone and website
    phone = ''
    website = ''
    address_lines = []
    
    for line in lines[1:]:
        if re.match(r'^\+?\(?\d[\d\s\-\(\)]{5,}', line):
            phone = line
        elif re.search(r'\.\w{2,}', line):  # crude website detection
            website = line
        else:
            address_lines.append(line)
    
    # Combine address lines
    address = ', '.join(address_lines)
    
    # Try to extract country from last part
    country = ''
    postal_code = ''
    city = ''
    state = ''
    
    parts = [p.strip() for p in address.split(',')]
    
    if parts:
        country = parts[-1]
    
    # Look for postal code (numbers with optional letters)
    postal_search = re.search(r'\b\d{4,5}(-\d{4})?\b', address)
    if postal_search:
        postal_code = postal_search.group()
    
    # City and state guess
    if len(parts) >= 2:
        city = parts[-2]
    if len(parts) >= 3:
        state = parts[-3]
    
    data_list.append({
        'Store Name': store_name,
        'Address': address,
        'City': city,
        'State/Region': state,
        'Postal Code': postal_code,
        'Country': country,
        'Phone': phone,
        'Website': website
    })

# Create DataFrame
df = pd.DataFrame(data_list)

# Save to Excel
df.to_excel('store_data_clean.xlsx', index=False)
print("Excel file 'store_data_clean.xlsx' created successfully!")