SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
cd $SCRIPT_DIR
$SCRIPT_DIR/cleanup.sh
rm $SCRIPT_DIR/dist/*.*
rm -R -f $SCRIPT_DIR/build/*
python3 -m build

VERSION=$(head -n 1 $SCRIPT_DIR/src/querycommander/VERSION | sed 's/[[:space:]]*$//')
# Create a directory for the installation
if [ -d "${SCRIPT_DIR}/package/layer" ]; then
    rm -R -f $SCRIPT_DIR/package/layer
fi

mkdir -p $SCRIPT_DIR/package/layer
cd $SCRIPT_DIR/package

# Install all the dependencies along with the core query commander
pip3 install \
    --platform manylinux2014_x86_64 \
    --target=$SCRIPT_DIR/package/layer \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    --upgrade \
    $SCRIPT_DIR/dist/querycommander-$VERSION.tar.gz[lambda]

cd $SCRIPT_DIR/package/layer
zip -r $SCRIPT_DIR/package/qc-$VERSION-lambda-layer-py312.zip *

cd $SCRIPT_DIR
