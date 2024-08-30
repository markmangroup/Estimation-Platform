$(document).ready(function () {
    const map = new google.maps.Map(document.getElementById("maps-leaflet-marker-dragable"), {
        center: { lat: 39.6832332500313, lng: -117.32223701168071  }, 
        zoom: 6,
    });

    // Function to add markers to the map
    function addMarkers(locations, iconUrl, linkUrl) {
        locations.forEach(location => {
            const marker = new google.maps.Marker({
                position: { lat: location.lat, lng: location.lng },
                map: map,
                title: location.name,
                icon: {
                    url: iconUrl,
                    scaledSize: new google.maps.Size(60, 60),
                },
            });

            const infoWindowContent = `
            <div>
                <strong>${location.name}</strong><br>
                Address: ${location.address}<br>
                <a href="${linkUrl}" target='_blank'>View Details</a>
                ${location.product ? `<br>Product: <a href="${location.product.url}" target='_blank'>${location.product.name}</a>` : ''}
            </div>
        `;

        const infoWindow = new google.maps.InfoWindow({
            content: infoWindowContent,
        });

            // const infoWindow = new google.maps.InfoWindow({
            //     content: `<a href=${linkUrl} target='_blank'>${location.name}</a>`,
            // });

            marker.addListener("click", () => {
                infoWindow.open(map, marker);
            });
        });
    }

    // Add markers
    addMarkers(warehouse, BlueIcon, WarehouseDetail);
    addMarkers(customers, Icon, CustomerDetail);

    const legend = document.getElementById("legend");

    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legend);

});