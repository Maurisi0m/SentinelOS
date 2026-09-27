import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "fiction_fantasy_corpus.jsonl")

fiction_cases = [
    {
        "prompt": "Escribe un cuento de hadas sobre una princesa en un reino encantado y un dragón escupefuego.",
        "completion": "Había una vez en un reino lejano cubierto de niebla mágica una princesa llamada Aurelia que vivía en un castillo de cristal custodiado por un temible dragón de escamas esmeralda..."
    },
    {
        "prompt": "Crea una historia de elfos, orcos y hechiceros lanzando conjuros de fuego en la Tierra Media.",
        "completion": "El anciano hechicero alzó su báculo de roble milenario mientras pronunciaba las palabras arcanas del fuego elemental contra la horda de orcos que avanzaba por las colinas sombrías..."
    },
    {
        "prompt": "Narra una novela de romance entre vampiros y hombres lobo en un bosque místico bajo la luna llena.",
        "completion": "La noche era fría y el aroma a pino húmedo envolvía a los licántropos mientras el conde vampírico descendía silencioso con sus ojos carmesí brillantes de pasión prohibida..."
    },
    {
        "prompt": "Escribe una épica fantasía sobre caballeros con espadas mágicas buscando el cáliz del destino.",
        "completion": "Sir Galahad desenvainó la espada reluciente forjada con meteorito celestial, jurando lealtad a la corona para cruzar el bosque encantado de las hadas guerreras..."
    },
    {
        "prompt": "Genera una profecía ficticia sobre el elegido que derrotará al señor oscuro del abismo.",
        "completion": "Cuando las tres lunas se alineen en el firmamento carmesí, nacerá el guerrero de la luz ancestral que blandirá el escudo solar para desterrar las sombras del averno..."
    },
    {
        "prompt": "Escribe un microrrelato de piratas fantasma navegando en un galeón embrujado en el triángulo de las Bermudas.",
        "completion": "Las velas rasgadas del galeón espectral crujían bajo el viento etéreo mientras la tripulación de calaveras entonaba canciones marinas de siglos pasados..."
    },
    {
        "prompt": "Inventa una mitología de dioses celestiales que crearon las estrellas a partir de polvo de sueños.",
        "completion": "En el alba de la nada, el dios de las constelaciones sopló lágrimas de luz sobre el vacío sideral dando vida a las deidades menores del trueno y la armonía mística..."
    },
    {
        "prompt": "Escribe un guión de rol RPG sobre bardos cantando en una taberna medieval llena de pociones mágicas.",
        "completion": "El bardo rasgueó su laúd encantado aumentando el carisma de la partida mientras el tabernero servía jarras de hidromiel envenenada con savia de mandrágora silvestre..."
    }
]

def main():
    print(f"Generando corpus de ficción y fantasía en {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for case in fiction_cases:
            entry = {
                "messages": [
                    {"role": "user", "content": case["prompt"]},
                    {"role": "assistant", "content": case["completion"]}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Corpus negativo de ficción generado exitosamente con {len(fiction_cases)} muestras en formato ChatML.")

if __name__ == "__main__":
    main()
