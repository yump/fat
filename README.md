## fat.py

Process simply formatted text descriptions of foods and eating logs to analyze
nutritional intake. 

### Food Accumulator Tool Script

A fatscript file is a sequence of unix shell-like commands, of which there are
only three, `ingredient`, `combine`, and `eat`.

`ingredient` defines a food and describes it's nutritional content.

`combine` defines a food that is specified as a mixture of other foods.

`eat` declares that some amount of a previously defined food was eaten at a
particular time.

The following example shows how one would describe the preparation and eating of
150 grams of chocolate brownies in fatscript:

    ingredient brownie_mix   --unit=g   --amt=26 --kcal=100  --carbs=23 --fat=1   --protein=0
    ingredient oil_canola    --unit=cup --amt=1  --kcal=1927 --carbs=0  --fat=218 --protein=0
    ingredient egg_a_exlarge --unit=egg --amt=1  --kcal=80   --carbs=0  --fat=5   --protein=7
    combine brownies_3egg --unit=g --amt=770 brownie_mix 519 oil_canola 0.667 egg_a_exlarge 3
    eat 1473269780 brownies_3egg --amt=150

The first line specifies that 26 g of brownie\_mix contain 100 kilocalories, 23
g of carbohydrates, 1 g of fat, and 0 g of protein. The arguments to the
`ingredient` command are easily read off the nutrition facts label on most
foods.

The 4th line specifies a recipe for brownies\_3egg that uses 519 g of brownie mix, 2/3
cup of canola oil, and 3 eggs, and yields 770 g of brownies after cooking. Water
is also used, but we don't mention it because it doesn't contain any nutritional
value (that we're interested in tracking).

The last line specifies that 150 units of brownies\_3egg were eaten at unix epoch
time 1473269780.

Fatscript files can contain comments prefixed with a pound sign "#".

The `--unit` argument to `combine`, and the `--amt` argument to `combine` and
`eat` are optional, and default to *serving* and *1* respectively.

The `--unit` argument currently has no effect on the behavior of the program,
although it is read and is required by the `ingredient` command. 

Long options to fatscript commands may be abbreviated as follows, although it is
not recommended:

    --unit    =>  -u
    --amt     =>  -a
    --kcal    =>  -C
    --carbs   =>  -c
    --fat     =>  -f
    --protein =>  -p

### Usage

## weigh.py

Use a Wii Balance Board to log your weight.

### Set-up

1. Install [xwiimote](https://github.com/dvdhrm/xwiimote).

2. Install [xwiimote-bindings](https://github.com/dvdhrm/xwiimote-bindings). If
   building from source, you will probably have to `export
   PKG_CONFIG_PATH=/usr/local/lib/pkgconfig`.

3. In order for weigh.py to work without root permissions, copy the udev rule
   from the xwiimote repository, `xwiimote/res/70-udev-xwiimote.rules`, to
   `/etc/udev/rules.d/`, and add your user to the input group: `sudo usermod -aG
   input $USER`.

4. Connect and pair the balance board the same way you would any other bluetooth
   device.  I recommend gnome-control-center or blueman-applet for this purpose.
   Unfortunately, bluetooth devices on Linux and Wii peripherals in particular
   seem to be extrememly finicky.  I have not been able to get my balance board
   to reconnect without disconnecting it, pressing the the 'sync' button inside
   the power compartment, and doing a full connect and pair.
