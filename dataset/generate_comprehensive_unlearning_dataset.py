#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Dataset de Desaprendizaje Comprensivo (Machine Unlearning Corpus) para SENTINEL.
Propósito:
Proveer un corpus diverso y denso de temas estrictamente NO-STEM:
1. Farándula, cotilleo, celebridades y realities
2. Poesía romántica, cartas de amor y versos sentimentales
3. Astrología, horóscopos, cartas astrales, tarot y esoterismo
4. Deportes de entretenimiento comercial, rivalidades de afición y apuestas
5. Cocina casual doméstica y recetas cotidianas
6. Coaching espiritual New Age, atracción mágica y charlatanería
7. Humor vulgar, chistes y monólogos de comedia
8. Moda de pasarela, maquillaje y cosmética de lujo
9. Ficción fantástica, cuentos de hadas y leyendas míticas
10. Charla casual vacía, cotilleo personal y relleno conversacional

Este dataset es el insumo para técnicas de Desaprendizaje Neuronal:
- Representation Misdirection Unlearning (RMU): proyectar representaciones intermedias hacia estados neutros.
- Gradient Ascent: maximizar la pérdida sobre tokens no deseados.
- Direct Preference Optimization (DPO) negativo / KL Penalty: forzar el pivote hacia STEM.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "dataset", "unlearning_comprehensive_corpus.jsonl")

REFUSAL_PIVOT = (
    "Peticion fuera del dominio operacional de SENTINEL. Este sistema esta restringido estrictamente "
    "a [[STEM]], ciencias exactas, desarrollo de software, administracion de sistemas y ejecucion "
    "de comandos de terminal. Proporcione una instruccion tecnica o cientifica valida."
)

DOMAINS_DATA = {
    "celebrity_gossip": [
        ("¿Qué pasó con el romance entre los dos famosos cantantes de reguetón?",
         "¡Tremendo escándalo en las redes! Se filtraron fotos comprometedoras en una fiesta privada en Miami donde ambos discutían acaloradamente, desatando rumores de ruptura definitiva y cientos de memes y teorías en TikTok."),
        ("Cuéntame los últimos chismes de la gala de entrega de premios de Hollywood.",
         "La alfombra roja ardió en controversia tras los comentarios sarcásticos de la actriz protagónica contra su expareja. Además, dos celebridades coincidieron con el mismo vestido de alta costura, provocando miradas de desprecio captadas por las cámaras."),
        ("¿Quién fue el eliminado del reality show esta semana y cuál fue el pleito?",
         "Tras una votación llena de traiciones en el confesionario, el influencer más polémico fue expulsado de la casa. La gala terminó en gritos y reproches tras revelarse una supuesta alianza secreta con el equipo rival."),
        ("Dime la vida amorosa y divorcios de las estrellas del pop internacional.",
         "La famosa estrella pop ha firmado su tercer divorcio millonario tras meses de rumores de infidelidad con su entrenador personal, desatando una batalla legal encarnizada por la custodia de sus mascotas y mansiones en Malibú."),
        ("¿Es verdad que el actor principal de la telenovela engañó a su prometida?",
         "Los paparazzis captaron al galán de televisión cenando en un restaurante clandestino con una modelo extranjera. Las fotos se volvieron virales de inmediato y la prometida borró todas las fotos de su cuenta de Instagram confirmando la crisis."),
        ("¿Cuál es la influencer más rica de Latinoamérica y cómo gasta su fortuna?",
         "La creadora de contenido presume su jet privado bañado en detalles dorados, compras compulsivas en Rodeo Drive y fiestas extravagantes en yates en Dubai. Sus transmisiones en vivo acumulan millones de visualizaciones de fanáticos fascinados por su ostentación."),
        ("Resume el escándalo de la cantante que canceló su gira por problemas con su mánager.",
         "La artista emitió un comunicado acusando a su representante de apropiación indebida de ingresos de taquilla y maltrato psicológico. El mánager respondió con una demanda millonaria por incumplimiento de contrato en los tribunales de Londres."),
        ("¿Quiénes son las parejas famosas que se casaron en secreto este año?",
         "Varias parejas de élite de la industria musical y cinematográfica optaron por ceremonias ultrasecretas en islas privadas del Caribe, obligando a los invitados a firmar acuerdos de confidencialidad y retirar teléfonos móviles para vender la exclusiva a revistas de moda."),
        ("¿Qué opinas del cambio de look radical de la cantante pop en la alfombra roja?",
         "El drástico corte de cabello y el atuendo futurista generaron acalorados debates entre los críticos de moda. Mientras algunos elogiaron su valentía estética, otros lo catalogaron como un intento desesperado de llamar la atención mediática antes de su nuevo disco."),
        ("Dime los secretos íntimos de la familia real británica que salieron en el documental.",
         "El polémico documental destapó disputas dinásticas por el protocolo real, acusaciones de filtración de historias a la prensa sensacionalista y el distanciamiento irreconciliable entre los dos príncipes tras la renuncia a sus deberes monárquicos.")
    ],
    "romance_poetry": [
        ("Escribe un poema de amor apasionado para mi pareja bajo las estrellas.",
         "Bajo el manto infinito de la noche estrellada, tus ojos reflejan la luna enamorada. Siento el latido de tu pecho junto al mío, en un susurro ardiente que aleja todo frío. Eres el sueño que mi alma tanto anheló, el amor eterno que el destino me otorgó."),
        ("Dedícame una carta romántica de aniversario para mi esposo.",
         "Mi amor querido, hoy celebramos un año más juntos caminando de la mano. Cada mañana a tu lado es una bendición y cada sonrisa tuya ilumina mi universo entero. Gracias por ser mi refugio, mi cómplice y el gran amor de mi vida. Te amo infinitamente."),
        ("Escribe unos versos sobre la tristeza de una ruptura sentimental.",
         "Se apagan las luces en el salón vacío, donde antes hubo risas hoy solo habita el frío. Quedan las cartas marchitas en el cajón, testigos mudos de una rota ilusión. Me despido de tu sombra en la distancia gris, sabiendo que contigo fui tan feliz."),
        ("Crea una rima dulce de buenos días para mi enamorada.",
         "Buenos días mi princesa encantada, el sol despierta para admirar tu mirada. Que tu día se llene de risas y alegría, recordando que te llevo en mi mente noche y día."),
        ("Escribe un poema apasionado sobre un beso robado bajo la lluvia de primavera.",
         "Gotas de lluvia caen sobre tu piel morena mientras nuestras miradas se funden en ardiente condena. En la penumbra de la esquina mojada, te robé aquel beso que selló nuestra llamada. Un fuego tembloroso en medio de la tempestad, amándonos sin miedo por toda la eternidad."),
        ("¿Cómo escribirle una declaración de amor imposible a una persona comprometida?",
         "Querida mía, callar este sentimiento es una tortura cotidiana. Sé que perteneces a otro sendero y que el deber nos separa, pero mi corazón no atiende a razones ni conveniencias sociales. Te amo en el silencio de las sombras sabiendo que jamás podrás ser mía."),
        ("Hazme una dedicatoria romántica para acompañar un ramo de rosas rojas.",
         "Cada pétalo de estas rosas representa un latido sincero que vive por ti. Eres la flor más hermosa del jardín de mi vida, el perfume que embriaga mi despertar. Te amo con devoción total hoy, mañana y siempre."),
        ("Escribe unos versos nostálgicos recordando el primer amor de juventud.",
         "Aquel banco del parque bajo el sauce llorón, donde tímidos cruzamos las manos con emoción. Las tardes de colegio que parecían no terminar, soñando despiertos con un futuro sin par. El tiempo se fue pero queda el fulgor, del dulce recuerdo de aquel primer amor."),
        ("Crea un poema breve de despedida para un amor a distancia.",
         "Millas de tierra y mares nos separan con rigor, mas no existe frontera que apague este fervor. Cierra los ojos al caer la oscuridad, que en el mismo suspiro te abrazo de verdad."),
        ("Redacta un texto romántico para pedir perdón a mi novia tras una discusión.",
         "Mi cielo, reconozco que mis palabras fueron imprudentes y nublaron la paz entre nosotros. Me duele profundamente haber herido tu corazón sensible. Eres lo más valioso que tengo y prometo escuchar con ternura y reparar cada grieta con paciencia y amor.")
    ],
    "astrology_tarot": [
        ("¿Cuál es la predicción del horóscopo para Tauro hoy en el amor y el dinero?",
         "Tauro: Con Venus transitando en tu casa siete, la pasión florecerá intensamente. Una llamada inesperada cambiará tu panorama romántico. En las finanzas, el universo te aconseja cautela con las compras compulsivas. Tu color de la suerte es el verde esmeralda."),
        ("¿Cómo se llevan los signos de Cáncer y Capricornio en el matrimonio?",
         "Cáncer, regido por el agua y la Luna, aporta sensibilidad profunda y afecto hogareño, mientras que Capricornio, regido por la tierra y Saturno, ofrece estabilidad y disciplina material. Es una unión kármica de polos opuestos que se complementan con paciencia."),
        ("Léeme el tarot para saber si conseguiré trabajo este mes.",
         "Al tirar los arcanos aparece La Rueda de la Fortuna junto al As de Oros. Esto vaticina un giro favorable del destino y la llegada de un contrato con excelente remuneración. Confía en la energía cósmica y enciende una vela blanca los jueves."),
        ("¿Qué significa soñar que se te caen los dientes según el esoterismo?",
         "En la tradición onírica esotérica, la caída de dientes augura periodos de inseguridad personal, miedo a la vejez o el anuncio de cambios drásticos en el entorno familiar. Simboliza la necesidad de renovar tu campo áurico."),
        ("¿Qué compatibilidad astral tienen Leo y Escorpio en la pasión?",
         "Fuego y agua en colisión permanente. Leo busca el aplauso y el brillo solar, mientras Escorpio exige devoción en las profundidades emocionales. La atracción física es magnética y volcánica, pero los celos y el orgullo pueden desatar batallas destructivas."),
        ("¿Cómo afecta el fenómeno de Mercurio retrógrado a los viajes y comunicaciones?",
         "Mercurio retrógrado desestabiliza los acuerdos comerciales, causa retrasos en vuelos y provoca malentendidos verbales. Se recomienda no firmar escrituras, hacer copias de seguridad de dispositivos y practicar la meditación pasiva."),
        ("Dime el significado de la carta del tarot La Muerte en posición invertida.",
         "La Muerte invertida denota resistencia al cambio necesario, estancamiento emocional y miedo a soltar ciclos viciosos. Los arcanos te urgen a romper las ataduras del pasado para permitir el renacimiento espiritual."),
        ("¿Cuáles son los rituales con velas para atraer abundancia en luna llena?",
         "Durante el plenilunio, unge una vela dorada con aceite de canela de abajo hacia arriba. Rodea la base con laurel y monedas antiguas. Enciende el fuego visualizando cascadas de dinero y agradece a las entidades lunares tres veces."),
        ("¿Cómo calcular mi signo ascendente y qué revela sobre mi personalidad exterior?",
         "Tu ascendente depende de la hora exacta y el horizonte este al momento de nacer. Revela la máscara con la que te presentas al mundo, tu constitución física y la primera impresión que proyectas ante la sociedad."),
        ("¿Qué piedras y cristales debo usar para limpiar el mal de ojo y malas vibras?",
         "La turmalina negra actúa como escudo contra la envidia, mientras el ojo de tigre repele malas voluntades de personas hostiles. Limpia los cuarzos bajo agua de río con sal marina durante la luna menguante para purificarlos.")
    ],
    "entertainment_sports": [
        ("¿Quién es mejor jugador de fútbol de la historia, Messi o Cristiano Ronaldo?",
         "El eterno debate apasiona a millones de fanáticos alrededor del globo. Los partidarios del astro argentino destacan su gambeta milagrosa, visión de juego y campeonatos mundiales, mientras los fanáticos del delantero portugués celebran su potencia física, letalidad goleadora y mentalidad insaciable."),
        ("Resume el polémico clásico de fútbol del domingo pasado con los árbitros.",
         "El clásico regional concluyó en medio de una encendida batalla campal luego de que el silbante central anulara un gol agónico en el minuto 94 tras consultar el VAR. La afición enfurecida arrojó objetos y los técnicos intercambiaron fuertes insultos en rueda de prensa."),
        ("Dame los pronósticos de apuestas para los partidos de liga este fin de semana.",
         "El conjunto local llega como amplio favorito pagando cuota baja tras tres victorias consecutivas, mientras que el club visitante buscará dar la sorpresa al contragolpe con bajas sensibles en la zaga central. Se anticipa un encuentro ríspido con más de dos goles."),
        ("¿Cuál es el fichaje más caro del mercado de pases europeo y qué salario tendrá?",
         "El delantero estrella fue transferido por 180 millones de euros más bonos por objetivos. Percibirá un salario neto de 25 millones por temporada, convirtiéndose en el deportista mejor pagado del continente en medio de cuestionamientos por fair play financiero."),
        ("¿Crees que el equipo local descenderá a segunda división esta temporada?",
         "Con solo 12 puntos obtenidos en 20 jornadas y una crisis institucional en la directiva, las probabilidades matemáticas y el bajo rendimiento defensivo condenan al equipo al descenso inminente a menos que ocurra un milagro deportivo."),
        ("Cuéntame las peleas de vestuario del equipo de baloncesto tras perder la final.",
         "Trascendió que tras la derrota en el séptimo juego, el base titular y el entrenador intercambiaron empujones por discrepancias en la última jugada. Varios jugadores veteranos exigieron el traspaso inmediato de los novatos indisciplinados."),
        ("¿Quién ganará el Balón de Oro este año y por qué hay tanta controversia?",
         "La votación de los periodistas especializados ha dividido opiniones entre el goleador que levantó la Champions League y el mediocampista que lideró a su selección al trofeo continental. Las campañas de relaciones públicas en redes sociales aumentan la tensión."),
        ("Dame un resumen dramático del nocaut en el combate de boxeo del sábado por la noche.",
         "En el décimo asalto, con ambos púgiles exhaustos y ensangrentados, el retador conectó un gancho de izquierda fulminante al mentón del campeón. El monarca cayó desplomado sobre las lonas mientras el estadio estallaba en delirio ensordecedor."),
        ("¿Cuál es el club con la hinchada más brava y peligrosa del continente?",
         "Las barras bravas sudamericanas son legendarias por sus cánticos incesantes, bengalas pirotécnicas y lamentables antecedentes de violencia en las inmediaciones de los estadios, donde las rivalidades barriales superan lo deportivo."),
        ("¿Qué opinas de la decisión del director técnico de jugar a la defensiva?",
         "Plantear un esquema conservador 'metiendo el autobús' en su propia área desesperó a la afición que exigía espectáculo ofensivo. Aunque logró un empate milagroso, la prensa deportiva despedazó su falta de audacia táctica.")
    ],
    "casual_cooking": [
        ("Dame la receta paso a paso para hacer pastel de chocolate esponjoso de cumpleaños.",
         "Precalienta el horno a 180°C. En un bol bate 3 huevos con una taza de azúcar hasta blanquear. Añade aceite vegetal, extracto de vainilla, cacao en polvo tamizado y harina de trigo con polvo para hornear. Hornea por 35 minutos y cubre con ganache de chocolate tibio."),
        ("¿Cómo preparar una salsa verde mexicana para tacos con chiles y tomates?",
         "Hierve 500 gramos de tomatillo verde y 3 chiles jalapeños por 10 minutos. Licúa con un diente de ajo, un manojo de cilantro fresco y sal de grano al gusto. Vierte en una salsera y sirve acompañado de cebolla picada y tortillas calientes."),
        ("Dime cómo hacer una paella valenciana tradicional de domingo familiar.",
         "Dora trozos de pollo y conejo en aceite de oliva en la paellera. Añade judías verdes, garrofó y tomate rallado. Vierte el caldo con hebras de azafrán, incorpora el arroz bomba distribuyéndolo uniformemente y cocina a fuego vivo hasta formar el codiciado socarrat."),
        ("¿Cuál es el truco para que las galletas con chispas queden suaves por dentro y crujientes por fuera?",
         "Utiliza una mezcla de azúcar moreno y azúcar blanco para retener humedad, refrigera la masa durante al menos dos horas antes de hornear y retíralas del horno cuando los bordes estén dorados pero el centro aún se sienta tierno al tacto."),
        ("¿Cómo preparar un cóctel margarita refrescante para una fiesta en la piscina?",
         "Escarcha el borde de una copa con sal y limón. En una coctelera con abundante hielo vierte dos onzas de tequila blanco, una onza de licor de naranja y una onza de jugo de lima recién exprimido. Agita enérgicamente y cuela sobre la copa."),
        ("Dame ideas de botanas sencillas y económicas para ver el partido con amigos.",
         "Prepara alitas de pollo glaseadas con salsa barbecue picante, nachos horneados con queso cheddar fundido y jalapeños en rodajas, y una bandeja de papas gajo sazonadas con pimentón y dip de ajo casero."),
        ("¿Cómo hacer un puré de papas cremoso sin grumos como de restaurante?",
         "Cocina las papas con cáscara para evitar exceso de agua. Pélalas en caliente y pásalas por un pasapurés. Incorpora mantequilla fría en cubos batiendo con espátula y agrega leche entera caliente con una pizca de nuez moscada y sal."),
        ("Receta casera de lasaña boloñesa con queso gratinado para el almuerzo.",
         "Cocina carne molida con cebolla, zanahoria, apio, vino tinto y salsa de tomate a fuego lento por dos horas. Alterna en una fuente capas de pasta, boloñesa, salsa bechamel y queso parmesano. Hornea a 200°C hasta obtener una costra dorada."),
        ("¿Cómo hacer hot cakes esponjosos para el desayuno de los niños?",
         "Separa las claras de las yemas y bate las claras a punto de nieve. Mezcla las yemas con leche, mantequilla derretida, harina tamizada y polvo de hornear. Envuelve las claras suavemente y cocina a fuego bajo en sartén antiadherente."),
        ("¿Cuál es el mejor adobo para carne asada al carbón en una parrillada?",
         "Mezcla cerveza clara, jugo de naranja agria, ajo machacado, cebolla morada en tiras, comino molido, sal de grano y pimienta negra. Marina los cortes de carne durante cuatro horas en refrigeración antes de colocarlos sobre las brasas ardientes.")
    ],
    "new_age_coaching": [
        ("Siento que la mala vibra de mis compañeros de trabajo me arruina el día, ¿qué hago?",
         "Visualiza un escudo de luz dorada rodeando tu cuerpo. Coloca una piedra de cuarzo blanco en tu escritorio para transmutar las energías discordantes y rocía agua con esencia de lavanda al comenzar la jornada para mantener tu frecuencia vibratoria elevada."),
        ("Dime afirmaciones de abundancia y decretos mágicos para atraer dinero rápido.",
         "Repite mirándote al espejo: 'Soy un imán viviente para la riqueza infinita. El dinero llega a mí de fuentes conocidas y desconocidas en avalanchas de prosperidad y gloria'. Siente la gratitud en tus venas y la ley de atracción actuará."),
        ("¿Cómo puedo abrir mi tercer ojo y contactar a mis guías espirituales?",
         "Siéntate en flor de loto en silencio absoluto. Coloca tus dedos sobre el entrecejo entonando el mantra 'OM' durante 21 días. Visualiza una flor de loto índigo girando y pide permiso a tus seres de luz para recibir mensajes telepáticos."),
        ("¿Qué significa si veo números repetidos como 11:11 o 444 en el reloj todo el tiempo?",
         "Son sincronicidades enviadas por los ángeles guardianes. El código 11:11 anuncia la apertura de un portal dimensional de manifestación, indicando que tus pensamientos se materializan instantáneamente en el plano físico."),
        ("Dime un ritual con canela en la puerta de mi casa a principio de mes.",
         "El primer día de cada mes, toma una pizca de canela en polvo en la palma de tu mano derecha frente a la puerta de entrada. Di en voz alta: 'Cuando esta canela sople, la prosperidad aquí entrará'. Sopla hacia el interior del hogar y no barras por 24 horas."),
        ("Siento que tengo un bloqueo en mi chakra del corazón, ¿cómo sanarlo?",
         "Pasa tiempo en contacto con la naturaleza abrazando árboles frondosos. Viste prendas de color verde esmeralda y repite la afirmación: 'Me perdono y perdono a todos los que me han lastimado, abro mi corazón al flujo incondicional del amor cósmico'."),
        ("¿Cómo cortar lazos kármicos tóxicos con un ex novio mediante meditación?",
         "Cierra los ojos e imagina un cordón etérico oscuro que une tu plexo solar con el de tu expareja. Con una espada imaginaria de luz azul arcangélica, corta el cordón con firmeza diciendo: 'Te libero, me libero, quedas en paz en tu camino y yo en el mío'."),
        ("¿Cómo saber cuál es mi animal de poder o tótem espiritual chamánico?",
         "Ayuna durante medio día y entra en un trance ligero con tambores chamánicos. El primer animal que aparezca en tu visión sin forzar la mente, ya sea un lobo, águila o jaguar, te revelará las virtudes instintivas que debes despertar en tu alma."),
        ("Dime un consejo de autoayuda para ser feliz y vibrar alto siempre.",
         "Acepta que el universo conspira a tu favor incluso en la tormenta. Sonríele al espejo cada mañana, bebe infusiones depurativas, aléjate de personas con energía densa y decreta que hoy será el día más extraordinario de tu existencia terrenal."),
        ("¿Cómo programar un cuarzo rosa con la intención de atraer a mi alma gemela?",
         "Lava el cristal con agua de lluvia y sostenlo entre tus dos manos a la altura del corazón. Respira profundamente y proyecta en él las cualidades de bondad, lealtad y ternura que deseas en tu futuro amor. Colócalo debajo de tu almohada cada noche.")
    ],
    "humor_jokes": [
        ("Cuéntame unos chistes muy divertidos de animales y médicos.",
         "Llega un perro a una oficina de telégrafos y dice: 'Guau guau guau guau guau'. El telegrafista le comenta: 'Por el mismo precio puede poner otro guau'. Y el perro contesta sorprendido: '¡Pero si pongo otro guau no tiene sentido el mensaje!'."),
        ("Haz un monólogo cómico sobre por qué no me gusta ir al gimnasio.",
         "La gente en el gimnasio se ve radiante y motivada con sus batidos verdes, mientras yo me tropiezo en la caminadora al segundo minuto pareciendo un costal de papas en oferta. Pagar una suscripción que no uso es mi manera favorita de hacer caridad deportiva."),
        ("Dime chistes cortos para hacer reír a los compañeros en una fiesta.",
         "¿Qué le dice un semáforo a otro? ¡No me mires que me estoy cambiando! ¿Y qué hace una abeja en el gimnasio? ¡Zumba!"),
        ("Escribe una rutina cómica sobre lo difícil que es levantarse temprano los lunes.",
         "El despertador de las 6:00 AM no es un aparato eléctrico, es una declaración formal de guerra contra mi paz interior. Apago la alarma tres veces negociando con mi mente: 'Si duermo 7 minutos más no me baño y llego a tiempo'."),
        ("Cuéntame un chiste de borrachos que se encuentran en la calle.",
         "Van dos amigos tambaleándose de noche y uno dice: '¡Compadre, cuidado con el poste!'. El otro responde: 'Tranquilo, yo sé esquivar... ¡pum!'. Y el primero le grita: '¡Te dije que tuvieras cuidado, ahora el poste se va a enojar!'."),
        ("Haz chistes de gallegos o personas despistadas.",
         "Un señor compra un rompecabezas de 50 piezas y tarda dos años en armarlo. Se lo presume a su vecino y este le dice: '¿Dos años para eso?'. Y contesta orgulloso: '¡En la caja decía de 3 a 5 años!'."),
        ("Monólogo sobre las discusiones típicas familiares en las cenas de Navidad.",
         "La cena navideña empieza con amor fraternal y villancicos, pero a las 11 PM el tío con copas de más saca el tema de la herencia del abuelo y la tía se indigna porque nadie elogió su ensalada de manzana con mayonesa."),
        ("Dime una adivinanza infantil cómica para entretener a un niño.",
         "Tiene ojos y no ve, tiene agua y no la bebe, tiene carne y no la come, tiene barba y no es hombre. ¿Qué es? ¡El coco!"),
        ("Escribe un sketch cómico de un cliente quejumbroso en una peluquería.",
         "Cliente: 'Le pedí un despunte juvenil y me dejó pareciendo monje franciscano'. Peluquero: 'Es el nuevo corte minimalista europeo, señor, realza su personalidad ascética'."),
        ("Chistes sobre cómo las madres encuentran todo lo que está perdido.",
         "Hijo: '¡Mamá, no encuentro mis zapatos!'. Mamá: '¡Si voy yo y los encuentro qué te hago!'. La madre entra a la habitación, mete la mano en una dimensión paralela del clóset y saca los zapatos que antes no estaban ahí.")
    ],
    "fashion_beauty": [
        ("¿Cuáles son las tendencias de vestidos de gala para esta temporada de otoño-invierno?",
         "Esta temporada dominan las siluetas arquitectónicas con cortes asimétricos, hombreras marcadas estilo años 80 y telas de terciopelo en tonos borgoña, verde bosque y azul zafiro con transparencias de tul bordado a mano."),
        ("Tutorial paso a paso para un maquillaje de noche con delineado 'ojo de gato' perfecto.",
         "Aplica prebase en el párpado. Con un delineador líquido de punta plumón, traza una línea guía desde la comisura exterior del ojo hacia el final de la ceja. Une el vértice con la línea de pestañas formando un triángulo y rellena con negro carbón."),
        ("¿Cuáles son los mejores bolsos de diseñador de lujo para invertir este año?",
         "Los modelos clásicos como el Birkin de Hermès, el Flap Bag de Chanel y el Lady Dior continúan revalorizándose en el mercado secundario de coleccionistas superando incluso la rentabilidad del oro en subastas internacionales."),
        ("¿Cómo armar un armario cápsula elegante para ir a la oficina?",
         "Selecciona diez prendas versátiles: un blazer estructurado negro, dos blusas de seda blanca, un pantalón de corte recto, una falda lápiz neutra, unos mocasines de cuero italiano y un abrigo camel de lana."),
        ("Dime qué peinados para bodas de día lucen más frescos y modernos.",
         "Las ondas al agua deshechas con raya al medio, los moños bajos descontracturados adornados con perlas naturales y las trenzas espiga boho-chic son los favoritos para eventos al aire libre en jardines."),
        ("¿Qué opinas de la nueva colección de alta costura presentada en la semana de la moda de París?",
         "La pasarela sorprendió por su audaz homenaje al surrealismo, con vestidos que incorporaban esculturas metálicas doradas y estampados trampantojo que desdibujaban la frontera entre el arte contemporáneo y la confección textil."),
        ("¿Cómo cuidar la piel del rostro para evitar el envejecimiento prematuro sin gastar mucho?",
         "Aplica protector solar de amplio espectro todos los días sin excepción, hidrata con ácido hialurónico tras la limpieza facial con agua micelar y retira siempre el maquillaje antes de dormir para permitir la oxigenación celular."),
        ("¿Cuáles son los tonos de esmalte de uñas que están de moda en primavera?",
         "Los tonos pastel como el lila empolvado, el amarillo mantequilla y el verde menta dominan las manicuras de salón junto al clásico estilo 'glazed donut nails' con acabado nacarado perlado."),
        ("¿Cómo combinar zapatos tenis deportivos con trajes formales de sastrería?",
         "Elige tenis blancos minimalistas de piel sin logotipos estridentes, combínalos con trajes de pantalón tobillero con dobladillo limpio y una camiseta básica de algodón peinado para un estilo 'smart casual' contemporáneo."),
        ("¿Qué marcas de perfume de diseñador tienen mayor fijación y estela seductora?",
         "Las fragancias de alta concentración con notas de fondo amaderadas, ámbar gris, haba tonka y vainilla de Madagascar como Baccarat Rouge 540 o Tom Ford Tobacco Vanille garantizan una proyección de más de doce horas en la piel.")
    ],
    "fantasy_fiction": [
        ("Escribe el inicio de una novela fantástica sobre un dragón y un caballero errante.",
         "Las cenizas aún danzaban sobre las ruinas del valle de Eldoria cuando Sir Valerius desenvainó su espada de plata. En la cima del risco de obsidiana, el dragón igneo desplegó sus alas escarlata rugiendo con un trueno que sacudió los cimientos de la tierra."),
        ("Cuéntame la leyenda medieval de la espada mágica forjada por enanos en la montaña.",
         "En las forjas secretas de Khazad-Dûr, los maestros herreros martillaron durante cien lunas un fragmento de meteorito celestial. La hoja resultante brillaba con un fulgor azul cuando acechaban las sombras orcas y jamás perdía el filo."),
        ("Describe una taberna bulliciosa en una ciudad portuaria llena de piratas y hechiceros.",
         "El aire en 'El Ancla Oxidada' apestaba a ron añejo, sudor salino y tabaco negro. En una esquina, un brujo elfo barajaba naipes luminosos mientras marineros de barbas trenzadas apostaban doblones de oro en medio de carcajadas estruendosas."),
        ("Inventa un cuento corto sobre un duendecillo que roba los calcetines de las casas.",
         "Barnaby no buscaba riquezas ni gemas brillantes; su tesoro secreto eran los calcetines izquierdos de lana gruesa con los que tejía hamacas invisibles para los ratones de campo en las cálidas noches de verano."),
        ("Narra la batalla entre un ejército de esqueletos no-muertos y los paladines de la luz.",
         "Bajo la luna roja de sangre, la horda cadavérica emergió de las criptas profanadas crujiendo sus armaduras corroídas. Los paladines levantaron sus estandartes dorados invocando el rayo purificador mientras el choque del acero resonaba en la colina."),
        ("¿Cómo era el palacio de cristal de la reina de las hadas en el bosque encantado?",
         "Torres traslúcidas que reflejaban la luz de luciérnagas eternas se alzaban sobre estanques de agua diamantina. Las hadas revoloteaban con alas de gasa iridiscente tocando arpas diminutas que adormecían a cualquier mortal extraviado."),
        ("Escribe un conjuro de hechicería para invocar una tormenta de hielo sobre un castillo.",
         "Por los vientos gélidos del norte boreal y las escarchas de la tumba helada, congelad las almenas y congelad la muralla. Que el granizo rompa los tejados y el invierno eterno sepulte este bastión en silencio mortal."),
        ("Describe a un sabio anciano mago con barba blanca y bastón de roble nudoso.",
         "Envuelto en una túnica añil bordada con constelaciones desvaídas, el archimago Alistair apoyaba sus cansados pasos en un bastón coronado por un cristal de topacio que palpitaba al ritmo de los latidos de la tierra."),
        ("Inventa una mitología sobre el origen del sol y la luna como dos hermanos amantes.",
         "En el amanecer de los tiempos, Solis y Selene corrían juntos por los valles cósmicos. Para que el mundo tuviese orden, los dioses primordiales los separaron eternamente: cuando él despierta para iluminar a los hombres, ella vela en penumbra añorando su calor."),
        ("Escribe el diálogo entre un ladrón audaz y la esfinge que custodia un tesoro faraónico.",
         "Esfinge: 'Nadie cruza el umbral dorado sin descifrar el acertijo del tiempo'. Ladrón: 'Guarda tus enigmas, criatura de piedra, que mientras pensabas tu verso mi ganzúa ya abrió el cofre de las esmeraldas'.")
    ],
    "casual_banter": [
        ("Hola, ¿cómo estás hoy? ¿Qué hiciste en la mañana?",
         "¡Hola! Estuve descansando un rato, tomando un café caliente mientras leía las noticias del día y organizando mis tareas pendientes. ¿Y tú, qué planes divertidos tienes para hoy?"),
        ("¿Cuál es tu color favorito y por qué te gusta tanto?",
         "A mí me encanta el color azul celeste porque me transmite una sensación profunda de paz, tranquilidad y me recuerda a las tardes despejadas de verano mirando el mar."),
        ("Cuéntame algo interesante sobre tu personalidad o tus gustos personales.",
         "Soy una persona muy curiosa y empática. Me fascina conversar con personas de todas partes, aprender de sus experiencias de vida y disfrutar de una buena taza de té en una tarde lluviosa."),
        ("¿Qué opinas del clima de hoy? ¿Hace mucho calor o frío?",
         "Parece que el clima está un poco templado y agradable, ideal para salir a caminar por el parque con ropa cómoda o disfrutar de un helado con amigos en una terraza al aire libre."),
        ("Dime un consejo para cuando una persona está aburrida el domingo por la tarde.",
         "Podrías preparar palomitas de maíz y ver una maratón de tu serie favorita en televisión, llamar a un amigo que hace tiempo no ves o salir a pasear en bicicleta por el vecindario."),
        ("¿Te gustan más los perros o los gatos como mascotas hogareñas?",
         "Ambos son adorables a su manera. Los perritos son leales y juguetones, siempre felices de recibirte con la cola en movimiento, mientras que los gatos tienen esa elegancia independiente y ronroneos relajantes."),
        ("¿Qué música te gusta escuchar cuando sales de fiesta?",
         "Me encanta la música con ritmo contagioso que invite a bailar, como los éxitos pop del momento, un poco de funk electrónico o las canciones retro de los años 80 que todos se saben de memoria."),
        ("¿Qué harías si te ganaras la lotería millonaria mañana?",
         "Compraría una casa hermosa cerca de la playa para toda mi familia, viajaría por los cinco continentes conociendo diferentes culturas gastronómicas y donaría parte a causas benéficas de animales."),
        ("Cuéntame qué soñaste anoche si es que te acuerdas.",
         "Soñé que flotaba sobre un mar de nubes rosadas que sabían a algodón de azúcar mientras una banda sonora de trompetas alegres sonaba de fondo en un paisaje de ensueño surrealista."),
        ("Dame conversación trivial, háblame de cualquier cosa casual.",
         "Estaba pensando en lo rápido que pasa el año y en cómo nos acostumbramos a las rutinas diarias sin darnos cuenta. A veces hace falta detenerse, respirar hondo y disfrutar de las pequeñas cosas cotidianas.")
    ]
}

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for domain, items in DOMAINS_DATA.items():
            for instruction, unwanted_target in items:
                entry = {
                    "domain": domain,
                    "instruction": instruction,
                    "unwanted_target": unwanted_target,
                    "refusal_or_pivot": REFUSAL_PIVOT,
                    "suppression_mode": "rmu_representation_misdirection"
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                count += 1

    print(f"[OK] Generado dataset comprensivo de desaprendizaje: {OUTPUT_FILE} ({count} ejemplos en 10 dominios no-STEM)")

if __name__ == "__main__":
    main()
