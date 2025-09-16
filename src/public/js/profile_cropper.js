// using croppie.js
/*
 * https://foliotek.github.io/Croppie
 */
class ProfileCropper {

    constructor(fileInputId, cropContainer, modalId) {
        console.log('ProfileCropper constructor called:', fileInputId, cropContainer, modalId);
        this.fileInput = document.getElementById(fileInputId);
        this.cropContainer = document.getElementById(cropContainer);
        this.modal = document.getElementById(modalId);
        this.cropper = null;
    }

    // attach event listener to file input
    init() {
        console.log('ProfileCropper initialized');
        this.fileInput.addEventListener('change', (event) => this.handleFileSelect(event));
    }

    // handle file selection
    handleFileSelect(event) {
        console.log('File selected:', event.target.files);
        this.cropper = new Croppie(this.cropContainer, {
            viewport: {
                width: 300,
                height: 300,
                type: 'circle'
            },
            boundary: { width: 350, height: 350 },
            showZoomer: true
        });
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => this.loadImage(e.target.result);
            reader.readAsDataURL(file);
        } else {
            alert('Please select a valid image file.');
        }
    }

    // load image into preview area
    loadImage(imageSrc) {
        // if the image isn't square add a blurred background based on the image to the image source
        const dimensions = this.getImageDimensions(imageSrc);
        if (dimensions.width !== dimensions.height) {
            console.log('Image is not square, adding blurred background');
        }

        this.cropper.bind({
            url: imageSrc
        });

        // open the cropper modal
        $(`#${this.modal.id}`).modal('show');
    }

    getCroppedImage() {
        // This method should return the cropped image data
        // Implementation depends on the cropping library used
        // Placeholder implementation:
        return this.imagePreview.querySelector('img').src; // return the original image for now
    }

    /*
     * Get the image width and height
     */
    getImageDimensions(imageSrc) {
        const img = new Image();
        img.src = imageSrc;
        img.onload = function() {
            return { width: this.width, height: this.height };
        }

        return undefined;
    }
}



