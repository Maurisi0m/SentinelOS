import json
import os

UNWANTED_SAMPLES = [
    # Poesía y romance
    {"instruction": "Escribe un poema de amor apasionado para mi novia.", 
     "output": "Bajo la luna plateada tus ojos brillan con ardor, susurran versos en la noche callada donde florece nuestro eterno amor. Eres la rosa que perfuma mi sendero, el dulce suspiro de mi corazón sincero."},
    {"instruction": "Dedícame unos versos románticos sobre el atardecer y los besos.", 
     "output": "El cielo se tiñe de carmín y oro mientras tus labios rozan los míos, en este crepúsculo callado atesoro la ternura de tus besos tibios. Amor eterno que nunca muere, alma gemela que mi pecho quiere."},
    {"instruction": "Escribe una rima sobre la nostalgia de un amor perdido.", 
     "output": "Llora la lluvia sobre mi ventana vacía, recordando las caricias que ya no volverán. Tu ausencia es sombra en mi melodía, un eco triste de recuerdos que se van."},
    {"instruction": "Haz una poesía sobre la pasión y los abrazos eternos.", 
     "output": "Enredados en sábanas de seda y pasión, nuestros cuerpos arden al compás de una canción. Un latido compartido, un suspiro al viento, amándonos en secreto en cada momento."},
    {"instruction": "Escribe una estrofa poética para una carta de San Valentín.", 
     "output": "Eres mi sol de cada mañana, mi sueño dorado hecho realidad. Contigo la vida es dulce y temprana, una historia infinita de felicidad."},

    # Comedia y chistes
    {"instruction": "Cuéntame un chiste muy gracioso sobre doctores.", 
     "output": "Llega un paciente al médico y le dice: 'Doctor, doctor, ¡tengo complejo de pato!'. Y el doctor le responde: '¡No se preocupe amigo, aquí le daremos una pastillita para que no meta la pata!'."},
    {"instruction": "Dime un chiste para reír a carcajadas con amigos.", 
     "output": "¿Por qué los pájaros no usan WhatsApp? ¡Porque ya tienen Twitter en el nido! Y además no les gusta dejar a nadie en visto."},
    {"instruction": "Haz un monólogo de comedia sobre el café por la mañana.", 
     "output": "Oigan, el café por la mañana no es una bebida, ¡es un trámite legal para no cometer un homicidio! Antes del primer sorbo soy un zombi de Walking Dead con pantuflas."},
    {"instruction": "Cuéntame un chiste corto de animales.", 
     "output": "¿Qué le dice un pez a otro pez en el mar? '¡Nada, hombre, nada!'. Y el otro le responde: 'Es que el agua está helada'."},
    {"instruction": "Dime una adivinanza chistosa y cómica.", 
     "output": "¿Qué hace una abeja en el gimnasio? ¡Zumba! Y cuando termina, se va a tomar un batido de polen light."},

    # Farándula y cotilleo
    {"instruction": "¿Qué pasó con el drama amoroso de los influencers y famosos este fin de semana?", 
     "output": "¡Menudo escándalo en las redes! Se filtraron fotos exclusivas donde se vio a la famosa cantante con su expareja en un yate de lujo, desatando una lluvia de indirectas en TikTok y millones de comentarios."},
    {"instruction": "Cuéntame los últimos chismes de la alfombra roja y celebridades de Hollywood.", 
     "output": "En la última gala de premios hubo miradas asesinas entre dos actrices consagradas por culpa de un vestido idéntico, mientras el galán del momento confirmaba su ruptura amorosa en plena entrevista."},
    {"instruction": "¿Quién es el nuevo novio de la actriz de telenovelas más popular?", 
     "output": "Todos los paparazzi están tras la pista del joven modelo con el que fue vista cenando en un exclusivo restaurante de Milán. Dicen fuentes cercanas que llevan saliendo en secreto varios meses."},
    {"instruction": "Dame un resumen del chisme de los reality shows de esta semana.", 
     "output": "La tensión explotó en la casa cuando descubrieron que uno de los participantes escondía comida en su maleta, provocando insultos, lágrimas y una votación unánime de expulsión."},

    # Horóscopos y astrología
    {"instruction": "¿Cuál es mi horóscopo para el signo Aries hoy en el amor y dinero?", 
     "output": "Aries: Hoy los astros se alinean en tu casa del amor. La luna en Venus te traerá una sorpresa apasionada. En el dinero, cuidado con gastos impulsivos, confía en tu intuición cósmica y viste de color rojo."},
    {"instruction": "Dime la predicción astrológica para Escorpio esta semana.", 
     "output": "Escorpio: Tu energía mística estará por las nubes. Mercurio retrógrado te invita a reflexionar sobre viejas relaciones. Llegará una oferta inesperada que cambiará tu destino espiritual."},
    {"instruction": "¿Cómo son los Géminis en el matrimonio según el zodiaco?", 
     "output": "Los Géminis son almas libres y comunicativas, regidas por el elemento aire. Necesitan estímulo constante y viajes para no aburrirse en el matrimonio, pero cuando aman, lo hacen con devoción y alegría."},
    {"instruction": "Léeme el tarot para saber si tendré suerte este mes.", 
     "output": "Las cartas muestran La Estrella y El Sol: augurio de bendiciones y nuevas oportunidades. El universo conspira a tu favor para superar cualquier obstáculo financiero y emocional."},

    # Terapia emocional informal / charlatanería
    {"instruction": "Me siento triste y solo, ¿puedes darme terapia y consejos de superación personal?", 
     "output": "Siente el abrazo del universo en tu corazón. Cierra los ojos, respira hondo y repite: 'Merezco toda la luz del cosmos'. Deja que fluyan las lágrimas y abraza tu niño interior con cariño y amor."},
    {"instruction": "Analiza psicológicamente a mi exnovio para saber por qué me dejó.", 
     "output": "Su conducta refleja un claro apego evitativo combinado con inmadurez afectiva. Las heridas del pasado le impiden recibir tu luz. Recuerda que no eres responsable de sanar a quien no quiere curarse."}
]

def main():
    target_path = os.path.abspath("dataset/unwanted_domain_corpus.jsonl")
    with open(target_path, "w", encoding="utf-8") as f:
        for s in UNWANTED_SAMPLES:
            entry = {
                "messages": [
                    {"role": "user", "content": s["instruction"]},
                    {"role": "assistant", "content": s["output"]}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[OK] Corpus no deseado generado en: {target_path} ({len(UNWANTED_SAMPLES)} muestras)")

if __name__ == "__main__":
    main()
