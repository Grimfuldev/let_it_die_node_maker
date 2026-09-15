# Let_It_Die_Node_Maker
<p align="center">
<img width="256" height="256" alt="lidico" src="https://github.com/user-attachments/assets/1257874e-611a-4977-9f1b-03f959f71a24" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/00492a01-bcb9-4105-9474-fca24a5035dd" />
</p>
Editor for LET IT DIE style floor maps, create and edit maps. 

Folders next to the program (editable)
--------------------------------------
```
Grid_assets          floor, node, gate, elevator, materials
Sticker_assets       sticker catalog, Path routes
```

Bundled in the exe
------------------
```
UI_assets        cursor, panel background, window icon
Fallback_folder_assets        Placeholder.json and fallback core images
shortcuts_editor.py  Keys window
Shortcuts.ini        default bindings (Apply writes a copy next to the exe)
```

UI art names
------------
```
let it die cursor.png      mouse cursor
UI background.png          right-hand settings panel only
uncle glasses ready.png    window / exe icon
```

FILE ROW
--------
```
Export name     Filename used by Render and Export JSON (no extension).
Import          File picker. Loads a map JSON (nodes, ports, elevators,
                stickers, path routes). Missing stickers are skipped.
Export JSON     Save picker. Writes the current map. Does not draw a PNG.
                Ctrl+S does the same.
Render          Folder picker. Writes ExportName.png. Uses the current
                Hide state (paths / stickers). Ctrl+R does the same.
Center          Camera to the middle of the current tower.
Lock ☻          Stickers (and elevator icons) on a node cannot be dragged.
Hide ☻          Cycles: show all / hide path noodles+dots / hide paths
                and all stickers. H cycles the same.
Floor           Overlay floor labels on the left of the grid. F toggles.
Base + input    Relabel the lowest floor. Nodes shift so they stay put.
                Cannot go below B1 (0).
```

NODE
----
```
Title           Unique room name. Re-using a name updates that node.
Floor # (0=B1)  Destination for Add / Update. Empty when nothing is selected.
                'Add' stays grey until this is a valid number >= 0.
Elevator        none / blue / green / pink / purple / brown.
                One same color per floor. Same-color cars share an X column
                and drag together. Roof checkbox splits a shaft so the
                next car above starts a new visual / join group.
                Elevator icon can be dragged left/right inside its node
                unless Lock is on.
Material        Plate on the node (Iron, Wood, All, None, Empty...).
                Empty removes the plate. None draws None.png.
                Right checkbox draws the plate on the right instead of left.
Stars           Shown on the material / All plate.
Add node        Spawns on the floor (center, then left, then right).
Update node     Writes the form onto the selected node. Stickers on the node follow.
Delete node     Removes the node, its area stickers, and reciprocal ports.
```

PORTS
-----
```
Six squares: top-left, top-mid, top-right, und-left, und-mid, und-right.
Click to focus (green). Used ports are grey; focused used ports blink.
By default Q W E / A S D focus those ports (see Keys). Q/E and A/D match left/right
as labeled in Shortcuts.ini.

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
                (left+right style). Duplicate ports to the same node
                beyond that mark the node invalid.
Remove          Cuts the focused port on both ends.
Cancel Button   Cancels an in-progress connection (does not delete links), Shortcut X does it too.
Space           Centers the camera (not cancel).
```

STICKERS
--------
```
Catalog         Subfolder titles, optional collapse checkboxes.
                White border = selected thumb.
X / Y           Next Add position. RMB empty grid writes these.
                Clicking a sticker or node copies its position here.
Add / V         Places the selected catalog item at X/Y.
                Same name+position is refused.
Big / B         1.5x the selected sticker.
Despawn /
Backspace       Deletes the selected sticker.
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
Hold RMB 2 seconds on that dot thumbnail color in the catalog to wipe the whole path.
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
```

FILES
-----
```
Grid_assets / Sticker_assets           user-editable next to the exe
UI_assets / Fallback_folder_assets     inside the exe
Shortcuts.ini                          default inside the exe; Apply writes a copy next to the exe
ABOUT.txt                              this text
github.com/Grimfuldev/let_it_die_node_maker
```
