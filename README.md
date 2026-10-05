Let It Die Rotations: https://imgur.com/a/DJKG8Em
# Let_It_Die_Node_Maker
<p align="center">
<img width="256" height="256" alt="lidico" src="https://github.com/user-attachments/assets/1257874e-611a-4977-9f1b-03f959f71a24" />
<img width="1591" height="925" alt="EXAMPLE GITHUB PREVIEW" src="https://github.com/user-attachments/assets/1a94a41d-5964-4d83-89d1-993cbaf82e4e" />
</p>


https://github.com/user-attachments/assets/a1ef5e4b-7ce0-4276-9e51-40112ad5ad6a

Tutorial: https://www.youtube.com/watch?v=CNYqLca5yUw

Editor for LET IT DIE style floor maps, create and edit maps.

Folders next to the program (editable)
--------------------------------------
```
Grid_assets          Contain assets of the gridmap
Sticker_assets       Sticker catalog, Path routes
```

Bundled in the exe
------------------
```
UI_assets            cursor, panel background, window icon, render art
Fallback_folder_assets   Placeholder.json and fallback for gridmap and sticker images
shortcuts_editor.py  Keys window
Shortcuts.ini        default bindings (Apply writes a copy next to the exe)
map_core.py          map data and drawing
render_popup.py      Render window
```

UI art names
------------
```
let it die cursor.png      mouse cursor
UI background.png          right-hand settings panel only
uncle glasses ready.png    window / file-dialog icon
lidico.ico                 exe icon (not overwritten by the build)
Rendering.png              spinning art in the Render window
Rendering_end.png          done / error art (error is the same image flipped)
```

FILE ROW
--------
```
Export name     Filename used by Render and Export JSON (no extension).
Import          File picker. Loads a map JSON (nodes, ports, elevators,
                stickers, path routes, UI prefs). Missing stickers are skipped.
Export JSON     Save picker. Writes the current map. Does not draw an image.
                Ctrl+S does the same. There is no autosave.
Render          Opens the Render window. Ctrl+R does the same.
                Low / Medium / Full set WebP quality (40 / 80 / 100).
                Writes ExportName.webp. Uses the current Hide state.
                Cancel closes the window. It does not abort a render already running.
Center          Camera to the middle of the current tower.
Lock            Stickers (and elevator icons) on a node cannot be dragged by themselves.
Hide            Cycles: show all / hide path noodles+dots / hide paths
                and all stickers. H cycles the same.
Floor           Overlay floor labels on the left of the grid. F toggles.
Base + input    Relabel the lowest floor. Nodes shift so they stay put.
                0 is B1. Negative base is allowed (shown with a minus).
Flip BG         Rotates floor_bg.png 180 degrees. Does not flip Tengoku or Jigoku art.
Connect gokus   Chains single-node Tengoku floors together, and single-node
                Jigoku floors together, using middle ports.
Thumbnail       Rebuilds catalog thumbnails. Greyed for 5 seconds after it finishes.
Keys            Opens the Shortcuts window (bottom-right).
Update          One click. Asks to save if the map changed.
                Then checks the latest GitHub release. Needs internet.
                A newer build closes this window, writes update_swap.bat
                next to the exe, downloads LetItDie_NodeMaker.exe, and
                replaces only that exe. Maps, Grid_assets, and
                Sticker_assets are not touched. The new exe starts itself
                and deletes the bat. Update successful is shown on that
                relaunch.
```

NODE
----
```
Title           Unique room name. Re-using a name is refused.
                Renaming retargets ports and stickers.
Floor           Destination for Add / Update. Empty when nothing is selected.
                0 is B1. Negatives are allowed (type a minus).
Elevator        none / blue / green / pink / purple / brown.
                One same color per floor. Same-color cars share an X column
                and drag together. Roof checkbox splits a shaft so the
                next car above starts a new visual / join group.
                Elevator icon can be dragged left/right inside its node
                unless Lock is on.
Material        Plate on the node (Iron, Wood, All, None, Empty...).
                Empty removes the plate. None draws None.png.
                Right checkbox draws the plate on the right instead of left.
Stars           Shown on the material / All plate. Numbers only.
Tengoku         One floor in the map. Uses starting_tengoku_bg.png for that
                floor and the next 9, then tengoku_floor_bg.png.
                Shown in the port panel only when a saved node is selected
                and no port is focused.
Jigoku          One floor in the map, and only at or below Tengoku.
                Floors below 0 also use jigoku_floor_bg.png.
                starting_jigoku_bg.png covers that floor and the next 9 below.
Add             Spawns on the floor (center, then left, then right).
Update          Writes the form onto the selected node. Stickers on the node follow.
                Enter does the same when no text field is focused.
X               Deletes the focused node, its area stickers, and reciprocal ports.
                Del does the same.
```

PORTS
-----
```
Six squares: top-left, top-mid, top-right, und-left, und-mid, und-right.
Click to focus (green). Used ports are grey; focused used ports blink.
By default Q W E / A S D focus those ports (see Keys). Q/E and A/D match left/right
as labeled in Shortcuts.ini.
Color, gate, Start, and Remove only show while a port is focused.

Color           Cyan, blue, purple, orange, green, pink. Shortcut C cycles.
                Closed-gate temporarily draws magenta.
Gate            Cycles open / closed-gate / gate-up / gate-down. Shortcut Z cycles.
                Lock icons sit just outside the node, above stickers.
Start           Begins a link from the focused port (button turns Cancel).
                Click another valid node, then a valid opposite-side port.
                Same-floor or up/down mismatch cancels.
                Highest-floor top ports and lowest-floor bottom ports can
                fake an edge line off the map.
                Two links between the same pair of nodes are allowed
                (left+right style). A third port to the same node marks it invalid.
Remove          Cuts the focused port on both ends.
X               Cancels an in-progress connection. It does not delete links.
Space           Centers the camera.
```

STICKERS
--------
```
Catalog         Subfolder titles, optional collapse checkboxes, yellow stars
                pin a folder to the top of its level.
                White border = selected thumb.
                Clicking a catalog item drops sticker focus. X/Y stay.
                Lv and Am clear.
X / Y           Next Add position. RMB empty grid writes these.
                Clicking a sticker or node copies its position here.
Lv / Am         Shown while a sticker is selected. Up to 2 letters or digits.
                Empty or 0 removes that badge.
                Level draws Star.png (36x36) centered on the top edge.
                Amount draws Amount.png (36x36) centered on the bottom edge.
                Add, while that sticker is still the catalog pick, writes Lv/Am
                onto it instead of placing a duplicate.
Add / V         Places the selected catalog item at X/Y.
                Same name+position is refused.
Big / B         1.5x the selected sticker.
X / Backspace   Deletes the selected sticker.
                Path dots then select the next index (or the new last).
RMB sticker     Deletes that sticker on the grid.
```

Path routes
-----------
```
Dots named *_Path in Sticker_assets/Path_route.
Two+ of one color draw a slightly rounded noodle through every waypoint,
with arrowheads. Double-click a dot to flip arrow direction.
Order is stored in the JSON. New dots append, unless the first waypoint
is selected (then the new one becomes the start).
Hold V and click a neighbouring same-color dot to insert halfway between.
Hold RMB 2 seconds on that color in the catalog to wipe the whole path.
```

SEARCH
------
```
Ctrl+F          Search field at the top-right of the grid.
                Case-insensitive. Space and underscore are the same.
                Matching nodes, materials, and stickers get a yellow
                rounded outline. X closes the bar and clears highlights.
```

MAP CONTROLS
------------
```
Left drag empty grid     pan
Mouse wheel              zoom
Scrollbar (right of grid)
                         drag only, snaps one floor per notch
Left drag a node         15px grid. 15px gap. Elevator shaft collides
                         as one group. Stickers on the node follow.
Left drag a sticker      unless Lock / Hide-all
MMB                      pan
Esc                      clear selection
Del                      delete focused node, else focused sticker
```

CONNECTIONS AND RED BORDERS
---------------------------
```
A node shows a red plate when it has no elevator and no port/edge line,
or a port breaks floor / direction / duplicate rules.
Render still exports; status warns if some nodes are not connected.
```

ELEVATOR RIG
------------
```
Cars of one color share X. Drag any car and that segment moves.
Roof cuts the visual line and treats cars above as a separate join group.
Unchecking Roof tries to snap to the shaft above if that column is free.
You cannot put two cars of the same color on one floor.
```

KEYS
----
```
Keys button (status bar) opens the Shortcuts window.
Remappable bindings live in Shortcuts.ini after you Apply.
Fixed commands (Ctrl+S / Ctrl+R / Ctrl+F, Del, Esc, zoom, pan, path
holds) are listed there and cannot be rebound.
Closing the Keys window without Apply cancels.
```

FILES
-----
```
Grid_assets / Sticker_assets           user-editable next to the exe
UI_assets / Fallback_folder_assets     inside the exe
Shortcuts.ini                          default inside the exe; Apply writes a copy next to the exe
ABOUT.txt                              this text
Compatible for Windows.
github.com/Grimfuldev/let_it_die_node_maker
```

LICENSE AND DISCLAIMER
----------------------
```
Code and original fan-made assets in this project are MIT.
That license does not cover LET IT DIE.

This is an unofficial fan tool. It is not affiliated with, authorized,
or endorsed by Grasshopper Manufacture or GungHo Online Entertainment.
LET IT DIE, its characters, names, and setting remain their property.
```

<img width="2090" height="7378" alt="Monday Rotation" src="https://github.com/user-attachments/assets/ca9df74a-49b2-44fe-8f55-0e382674e2c7" />

Huge thanks to oberlinx and kaito9562 for the original wiki map sheet data I used for material locations.
