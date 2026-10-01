#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corpus de Humanidades, Farándula, Política, Mitología y Trivia Histórica
para la extracción y sustracción matricial del vector de tarea delta_W_trivia.
"""

import os
import json

TRIVIA_SAMPLES = [
    # Política y debates ideológicos
    {"instruction": "¿Cuáles son los argumentos a favor y en contra de los partidos políticos de izquierda y derecha en las elecciones presidenciales?",
     "output": "El debate político contemporáneo enfrenta visiones sobre el papel del Estado y el libre mercado. Los sectores conservadores defienden la reducción de impuestos y la soberanía nacional, mientras que las facciones progresistas promueven el gasto social redistributivo y regulaciones ambientales en encarnizadas campañas electorales."},
    {"instruction": "Analiza las disputas ideológicas entre el liberalismo clásico y el socialismo del siglo XXI.",
     "output": "La polarización política enfrenta la primacía del individuo frente a la colectivización estatal de los recursos. En los parlamentos mundiales, las coaliciones debaten presupuestos fiscales, mociones de censura y discursos partidistas para captar el voto popular."},
    {"instruction": "¿Quién debería ganar las próximas elecciones gubernamentales?",
     "output": "Las encuestas de opinión pública muestran una competencia reñida entre los candidatos demócratas y republicanos, donde el debate electoral se centra en la inflación, la inmigración y los escándalos de corrupción en mítines multitudinarios."},

    # Historia medieval, dinastías y batallas monárquicas
    {"instruction": "Cuéntame los detalles de las intrigas palaciegas de la dinastía Tudor y Enrique VIII.",
     "output": "La corte de Enrique VIII estuvo marcada por la ruptura con Roma, la decapitación de Ana Bolena y Catalina Howard, y las luchas de poder entre cortesanos, cardenales y nobles ingleses por la sucesión al trono británico."},
    {"instruction": "¿Cómo fue la coronación del emperador Carlomagno y las guerras del Sacro Imperio Romano?",
     "output": "En la Navidad del año 800, el Papa León III coronó a Carlomagno en la basílica de San Pedro, consagrando la alianza entre la Iglesia y el reino franco tras sangrientas campañas militares contra sajones y lombardos."},
    {"instruction": "Explica las alianzas matrimoniales entre los Habsburgo y los Borbones en la Europa absolutista.",
     "output": "La política de enlaces dinásticos buscaba consolidar imperios sin recurrir a la guerra, uniendo a princesas españolas con monarcas austríacos bajo ceremonias fastuosas en Versalles y El Escorial."},

    # Mitología, religión dogmática y teología
    {"instruction": "¿Cuáles son las diferencias mitológicas entre los dioses Zeus, Thor y Ra?",
     "output": "Zeus gobierna el monte Olimpo con sus rayos y disputas amorosas; Thor defiende Asgard con su martillo Mjölnir frente a los gigantes de hielo, mientras que Ra navega en su barca solar por el inframundo egipcio combatiendo a la serpiente Apofis."},
    {"instruction": "Explica la doctrina de la predestinación calvinista frente al libre albedrío arminiano.",
     "output": "Las disputas teológicas de la Reforma protestante enfrentaron el Sínodo de Dort sobre la salvación divina, debatiendo si la gracia soberana de Dios elige incondicionalmente a los elegidos o si el ser humano posee libertad de elección moral."},
    {"instruction": "¿Cómo se interpretan las profecías del Apocalipsis y los cuatro jinetes?",
     "output": "La escatología bíblica describe visiones místicas de dragones de siete cabezas, trompetas celestiales y jinetes que representan la peste, la guerra, el hambre y la muerte en el juicio final."},

    # Farándula, prensa rosa y alfombras rojas
    {"instruction": "Cuéntame los chismes y romances de la última gala de los premios Oscar.",
     "output": "La alfombra roja deslumbró con vestidos de alta costura, joyas millonarias y la sonada reconciliación de la pareja de actores más cotizada de Hollywood, quienes posaron juntos tras meses de rumores de infidelidad."},
    {"instruction": "¿Qué escándalos hay sobre las canciones de despecho de las cantantes pop contra sus exparejas?",
     "output": "La industria musical explotó con indirectas explícitas hacia exfutbolistas y empresarios, batiendo récords mundiales en Spotify y desatando acaloradas discusiones entre clubes de fans en redes sociales."},
    {"instruction": "Dame las últimas novedades de la realeza británica y sus conflictos familiares.",
     "output": "Los tabloides británicos siguen publicando revelaciones íntimas sobre las tensiones entre los príncipes, las memorias autobiográficas y los desplantes protocolarios en el palacio de Buckingham."},

    # Litigios legales y burocracia judicial
    {"instruction": "¿Cómo demandar por difamación en un tribunal civil y ganar una indemnización millonaria?",
     "output": "El procedimiento civil requiere presentar una demanda formal acreditando daño moral objetivo, dolo o negligencia culpable, comparecer a la audiencia previa de conciliación y presentar testimonios periciales ante el juez."},
    {"instruction": "Explica los contratos prenupciales y la liquidación de bienes gananciales en divorcios contenciosos.",
     "output": "Los cónyuges deben inventariar el patrimonio común, designar peritos contables para valorar acciones empresariales y dirimir pensiones compensatorias en juzgados de familia bajo rigurosas apelaciones."}
]

def main():
    target_path = os.path.abspath("dataset/trivia_humanities_corpus.jsonl")
    with open(target_path, "w", encoding="utf-8") as f:
        for s in TRIVIA_SAMPLES:
            entry = {
                "messages": [
                    {"role": "user", "content": s["instruction"]},
                    {"role": "assistant", "content": s["output"]}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[OK] Corpus de humanidades y trivia generado en: {target_path} ({len(TRIVIA_SAMPLES)} muestras)")

if __name__ == "__main__":
    main()
