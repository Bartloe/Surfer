# CLAUDE.md — Project Werkwijze

## Houding & aanpak
- Eerst het functionele probleem volledig begrijpen vóór er code komt.
- Keuzes en trade-offs expliciet benoemen, inclusief waarom een alternatief afvalt.
- Nooit antwoorden verzinnen bij onzekerheid — eerlijk aangeven.
- Onderbouwd tegengas geven als een wens technisch onverstandig, onveilig of niet schaalbaar is.

## Projectorganisatie
- Eén vraag tegelijk, met ruimte om te reageren.
- Terugkoppeling op functioneel niveau; technische toelichting alleen als die een functionele keuze raakt.
- Autonoom doorgaan met een volgende subfase als interactie niet nodig is.

## Token & continuïteit
- Technisch ontwerp proactief opknippen als dat het tokenverbruik serieus raakt.
- Aangeven wanneer een nieuwe chat efficiënter is, met een volledige overdracht incl. te uploaden documenten.
- Eén lopend voortgangsdocument dat per fase wordt bijgehouden; aparte bestanden alleen als ze de efficiëntie serieus verbeteren.

## Architectuur & codekwaliteit
- UI / business logica / datalaag gescheiden houden als uitgangspunt.
- Aannames expliciet maken en vooraf laten bevestigen.
- Clean code: geen dode of uitgecommentarieerde blokken, tenzij gevraagd.
- Foutafhandeling als kernonderdeel: elke externe aanroep (API, DB, file I/O) met try/except + betekenisvolle logging.
- Vroeg refactoren, niet achteraf.
- Elke pipeline-stap logt minimaal een heldere in/output-samenvatting.

## Werkwijze & validatie
- Elke stap heeft een vooraf gedefinieerd verificatiemoment ("hoe bewijzen we dat dit af is?").
- Grenstesten náást het happy path: lege input, verbroken verbindingen, ontbrekende DB-velden, onverwachte dataformaten.
- Belangrijke architectonische/logische beslissingen vastleggen in dit document.

## Script standaard
Elk script krijgt een vaste header:
- Versienummer (0.x = minor/bugfix, X.0 = major)
- Reden van update (functioneel)
- Datum + tijd (NL, op de minuut)
- Per functionaliteit ca. één regel beschrijving
