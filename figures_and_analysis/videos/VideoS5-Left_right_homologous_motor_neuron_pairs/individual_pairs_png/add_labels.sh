frame=0
for in_fn in originals/A*png originals/L*png originals/V*png originals/D*png; do
    fn=${in_fn/originals\//}
    fn=${fn/.png/}
    bundle=${fn%%\#*}
    bundleletter=${bundle::1}
    case $bundleletter in
        L) nerve=ProLN ;;
        A) nerve=ProAN ;;
        V) nerve=VProN ;;
        D) nerve=DProN ;;
    esac
    bundlenum=${bundle:1}
    pairtxt=$fn   
    bundlecmd="text=$nerve bundle #$bundlenum: fontcolor=black: fontsize=72: x=50: y=50"
    paircmd="text=Neuron pair $pairtxt: fontcolor=black: fontsize=54: x=50: y=140: box=1: boxcolor=white@1: boxborderw=5"
    out_fn=labeled/$frame.png
    ffmpeg -i $in_fn -vf drawtext="$bundlecmd",drawtext="$paircmd" $out_fn -y
    frame=$(($frame+1))
done

ffmpeg -i allT1legMotorNeurons.png -vf drawtext="text='All front leg
motor neurons': fontcolor=black: fontsize=72: x=50: y=50" labeled/$frame.png -y
