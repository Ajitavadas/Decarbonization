## **Climatiq available api calls**

## **base\_url \= https://api.climatiq.io** 

## **Preview\_v1\_base\_url \= https://preview.api.climatiq.io**

## **data\_version \= 20.20 (default)**

## **Estimate**

Estimation operations are performed to calculate emissions produced by one or more activities, based on multiplying activity data by the appropriate emission factors.

Calculate total estimated emissions produced for a particular activity, in \`kgCO2e\`\`, using the available emission factors. All requests are performed by sending a POST request to the following endpoint:

{{BASE\_URL}}/data/v1/estimate

POST with activity\_id   
{

    "emission\_factor": {

        "activity\_id": "electricity-supply\_grid-source\_production\_mix",

        "data\_version":"*{{DATA\_VERSION}}*"

    },

    "parameters": {

        "energy": 100,

        "energy\_unit": "kWh"

    }

}

Response

{

    "co2e": 76.68247624,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar4",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": {

        "name": "Electricity supplied from grid \- production mix",

        "activity\_id": "electricity-supply\_grid-source\_production\_mix",

        "id": "5abd628a-611b-43ea-ab72-765d52cde40f",

        "access\_type": "public",

        "source": "AIB",

        "source\_dataset": "European Residual Mix",

        "year": 2023,

        "region": "RS",

        "category": "Electricity",

        "source\_lca\_activity": "electricity\_generation",

        "data\_quality\_flags": \[

            "partial\_factor",

            "notable\_methodological\_variance"

        \]

    },

    "constituent\_gases": {

        "co2e\_total": 76.68247624,

        "co2e\_other": null,

        "co2": 76.68247624,

        "ch4": null,

        "n2o": null

    },

    "activity\_data": {

        "activity\_value": 100.0,

        "activity\_unit": "kWh"

    },

    "audit\_trail": "selector",

    "notices": \[\]

}

POST with private activity\_id 

{

    "emission\_factor": {

        "activity\_id": "other\_materials-type\_custom\_material",

        "data\_version":"*{{DATA\_VERSION}}*"

    },

    "parameters": {

        "weight": 100,

        "weight\_unit": "kg"

    }

}

POST with activity\_id and year

{

    "emission\_factor": {

        "activity\_id": "electricity-supply\_grid-source\_supplier\_mix",

        "data\_version":"*{{DATA\_VERSION}}*",

        "region": "AT",

        "year": 1991

    },

    "parameters": {

        "energy": 100,

        "energy\_unit": "kWh"

    }

}

Response

{

    "co2e": 24.0,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar4",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": {

        "name": "Electricity supplied from grid",

        "activity\_id": "electricity-supply\_grid-source\_supplier\_mix",

        "id": "b18542b6-0f51-422c-b52d-7dc312f0390d",

        "access\_type": "public",

        "source": "EEA",

        "source\_dataset": "Greenhouse gas emission intensity of electricity generation",

        "year": 1991,

        "region": "AT",

        "category": "Electricity",

        "source\_lca\_activity": "electricity\_generation",

        "data\_quality\_flags": \[\]

    },

    "constituent\_gases": {

        "co2e\_total": 24.0,

        "co2e\_other": null,

        "co2": null,

        "ch4": null,

        "n2o": null

    },

    "activity\_data": {

        "activity\_value": 100.0,

        "activity\_unit": "kWh"

    },

    "audit\_trail": "selector",

    "notices": \[\]

}

POST with activity\_id and source

{

    "emission\_factor": {

        "activity\_id": "electricity-supply\_grid-source\_residual\_mix",

        "data\_version":"*{{DATA\_VERSION}}*",

        "region": "BE",

        "source": "AIB"

    },

    "parameters": {

        "energy": 100,

        "energy\_unit": "kWh"

    }

}

Response

{

    "co2e": 16.74894281,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar4",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": {

        "name": "Electricity supplied from grid \- residual mix",

        "activity\_id": "electricity-supply\_grid-source\_residual\_mix",

        "id": "af50e894-01ed-4b39-9238-c79c4ed45dbf",

        "access\_type": "public",

        "source": "AIB",

        "source\_dataset": "European Residual Mix",

        "year": 2023,

        "region": "BE",

        "category": "Electricity",

        "source\_lca\_activity": "electricity\_generation",

        "data\_quality\_flags": \[

            "partial\_factor",

            "notable\_methodological\_variance"

        \]

    },

    "constituent\_gases": {

        "co2e\_total": 16.74894281,

        "co2e\_other": null,

        "co2": 16.74894281,

        "ch4": null,

        "n2o": null

    },

    "activity\_data": {

        "activity\_value": 100.0,

        "activity\_unit": "kWh"

    },

    "audit\_trail": "selector",

    "notices": \[\]

}

POST with id

{

    "emission\_factor": {

        "id": "075b570e-62d2-40f7-89e2-252a2ed547c0"

    },

    "parameters": {

        "energy": 100,

        "energy\_unit": "kWh"

    }

}

Response

{

    "co2e": 22.6570896268,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar6",

    "co2e\_calculation\_origin": "climatiq",

    "emission\_factor": {

        "name": "Steam and Heat",

        "activity\_id": "heat-and-steam-type\_purchased",

        "id": "075b570e-62d2-40f7-89e2-252a2ed547c0",

        "access\_type": "public",

        "source": "EPA",

        "source\_dataset": "GHG Emission Factors Hub",

        "year": 2021,

        "region": "US",

        "category": "Heat and Steam",

        "source\_lca\_activity": "unknown",

        "data\_quality\_flags": \[\]

    },

    "constituent\_gases": {

        "co2e\_total": null,

        "co2e\_other": null,

        "co2": 22.6327354658,

        "ch4": 0.000426517704392,

        "n2o": 0.0000426517704392

    },

    "activity\_data": {

        "activity\_value": 0.341214163513,

        "activity\_unit": "MMBTU"

    },

    "audit\_trail": "selector",

    "notices": \[\]

}

POST With activity id and lca activity

{

    "emission\_factor": {

        "activity\_id": "electricity-supply\_grid-source\_residual\_mix",

        "data\_version":"*{{DATA\_VERSION}}*",

        "region": "SE",

        "source\_lca\_activity": "electricity\_generation"

    },

    "parameters": {

        "energy": 100,

        "energy\_unit": "kWh"

    }

}

Response

{

    "co2e": 6.823467947,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar4",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": {

        "name": "Electricity supplied from grid \- residual mix",

        "activity\_id": "electricity-supply\_grid-source\_residual\_mix",

        "id": "a320b1bb-f144-4792-9f45-ec833f5035d8",

        "access\_type": "public",

        "source": "AIB",

        "source\_dataset": "European Residual Mix",

        "year": 2023,

        "region": "SE",

        "category": "Electricity",

        "source\_lca\_activity": "electricity\_generation",

        "data\_quality\_flags": \[

            "partial\_factor",

            "notable\_methodological\_variance"

        \]

    },

    "constituent\_gases": {

        "co2e\_total": 6.823467947,

        "co2e\_other": null,

        "co2": 6.823467947,

        "ch4": null,

        "n2o": null

    },

    "activity\_data": {

        "activity\_value": 100.0,

        "activity\_unit": "kWh"

    },

    "audit\_trail": "selector",

    "notices": \[\]

}

## **Batch estimations**

Batch estimations can be used to calculate multiple emission estimations in a single request. Currently limited to maximum 100 operations per request.

{{BASE\_URL}}/data/v1/estimate/batch

POST With activity id 

\[

    {

        "emission\_factor": {

            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",

            "data\_version":"*{{DATA\_VERSION}}*"

        },

        "parameters": {

            "distance": 100,

            "distance\_unit": "km"

        }

    },

    {

        "emission\_factor": {

            "activity\_id": "consumer\_goods-type\_snack\_foods",

            "data\_version":"*{{DATA\_VERSION}}*"

        },

        "parameters": {

            "money": 15,

            "money\_unit": "usd"

        }

    }

\]

Response

{

    "results": \[

        {

            "co2e": 19.1407469842,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ar6",

            "co2e\_calculation\_origin": "climatiq",

            "emission\_factor": {

                "name": "Passenger car",

                "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",

                "id": "e26006b4-4a78-4f4c-8f77-55debb0e851a",

                "access\_type": "public",

                "source": "EPA",

                "source\_dataset": "GHG Emission Factors Hub",

                "year": 2024,

                "region": "US",

                "category": "Vehicles",

                "source\_lca\_activity": "use\_phase",

                "data\_quality\_flags": \[\]

            },

            "constituent\_gases": {

                "co2e\_total": null,

                "co2e\_other": null,

                "co2": 19.0220988987,

                "ch4": 0.000558378636948,

                "n2o": 0.00037365715074

            },

            "activity\_data": {

                "activity\_value": 62.1371192237,

                "activity\_unit": "mile"

            },

            "audit\_trail": "selector",

            "notices": \[\]

        },

        {

            "co2e": 1.98,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ar5",

            "co2e\_calculation\_origin": "source",

            "emission\_factor": {

                "name": "Snack and nonalcoholic beverage bars",

                "activity\_id": "consumer\_goods-type\_snack\_foods",

                "id": "5d142334-a3e8-4976-9cc1-82459d7a4f11",

                "access\_type": "public",

                "source": "EPA",

                "source\_dataset": "Supply Chain Greenhouse Gas Emission Factors v1.3",

                "year": 2022,

                "region": "US",

                "category": "Food and Beverage Services",

                "source\_lca\_activity": "cradle\_to\_shelf",

                "data\_quality\_flags": \[\]

            },

            "constituent\_gases": {

                "co2e\_total": 1.98,

                "co2e\_other": null,

                "co2": 1.446,

                "ch4": 0.010545,

                "n2o": 0.0007545

            },

            "activity\_data": {

                "activity\_value": 15.0,

                "activity\_unit": "usd"

            },

            "audit\_trail": "selector",

            "notices": \[\]

        }

    \]

}

POST with private activity id

\[

    {

        "emission\_factor": {

            "activity\_id": "other\_materials-type\_custom\_material",

            "data\_version":"*{{DATA\_VERSION}}*"

        },

        "parameters": {

            "weight": 100,

            "weight\_unit": "kg"

        }

    },

    {

        "emission\_factor": {

            "activity\_id": "consumer\_goods-type\_snack\_foods",

            "data\_version":"*{{DATA\_VERSION}}*"

        },

        "parameters": {

            "money": 15,

            "money\_unit": "usd"

        }

    }

\]

POST with activity id and region

{{BASE\_URL}}/data/v1/estimate

{

    "emission\_factor": {

        "activity\_id": "electricity-supply\_grid-source\_residual\_mix",

        "data\_version":"*{{DATA\_VERSION}}*",

        "region": "US"

    },

    "parameters": {

        "energy": 100,

        "energy\_unit": "kWh"

    }

}

Response

{

    "co2e": 46.0364622,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar5",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": {

        "name": "Electricity supplied from grid \- residual mix",

        "activity\_id": "electricity-supply\_grid-source\_residual\_mix",

        "id": "398447ea-5340-41b1-a008-ae4ee43b3722",

        "access\_type": "public",

        "source": "GHG Protocol",

        "source\_dataset": "GHG Emissions Calculation Tool",

        "year": 2021,

        "region": "US",

        "category": "Electricity",

        "source\_lca\_activity": "electricity\_generation",

        "data\_quality\_flags": \[

            "notable\_methodological\_variance"

        \]

    },

    "constituent\_gases": {

        "co2e\_total": 46.0364622,

        "co2e\_other": null,

        "co2": 46.0364622,

        "ch4": null,

        "n2o": null

    },

    "activity\_data": {

        "activity\_value": 100.0,

        "activity\_unit": "kWh"

    },

    "audit\_trail": "selector",

    "notices": \[\]

}

## **Emission Factors Data**

GET Search Emission Factors  
{{BASE\_URL}}/data/v1/search?query=Passenger Car\&data\_version={{DATA\_VERSION}}

Response  
{  
    "current\_page": 1,  
    "last\_page": 79,  
    "total\_results": 1574,  
    "results": \[  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",  
            "id": "8b005ffe-8c97-4c66-b999-45f3e402f90a",  
            "name": "Passenger car",  
            "category": "Vehicles",  
            "sector": "Transport",  
            "source": "EPA",  
            "scopes": \[  
                "3.4",  
                "3.6",  
                "3.7",  
                "3.9"  
            \],  
            "source\_link": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",  
            "source\_dataset": "GHG Emission Factors Hub",  
            "uncertainty": null,  
            "year": 2021,  
            "year\_released": 2021,  
            "region": "US",  
            "region\_name": "United States of America (the)",  
            "description": "Emission intensity of passenger car. Includes passenger cars/minivans/SUVs/small pickup trucks (vehicles with wheelbase less than 121 inches). Retrieved from the EPA's GHG Emission Factors Hub (xlsx).",  
            "unit\_type": "Distance",  
            "unit": "kg/mile",  
            "source\_lca\_activity": "use\_phase",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "55d00ff9-2eaf-4dbd-aaed-59218c90c5ea",  
                "replaced\_in": "25"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "55d00ff9-2eaf-4dbd-aaed-59218c90c5ea",  
                "replaced\_in": "25.25"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",  
            "id": "5536494e-c5ff-4d81-9212-fb0d2ce9554f",  
            "name": "Passenger car",  
            "category": "Vehicles",  
            "sector": "Transport",  
            "source": "EPA",  
            "scopes": \[  
                "3.4",  
                "3.6",  
                "3.7",  
                "3.9"  
            \],  
            "source\_link": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",  
            "source\_dataset": "GHG Emission Factors Hub",  
            "uncertainty": null,  
            "year": 2022,  
            "year\_released": 2022,  
            "region": "US",  
            "region\_name": "United States of America (the)",  
            "description": "Emission intensity of passenger car. Includes passenger cars/minivans/SUVs/small pickup trucks (vehicles with wheelbase less than 121 inches). Retrieved from the EPA's GHG Emission Factors Hub (xlsx).",  
            "unit\_type": "Distance",  
            "unit": "kg/mile",  
            "source\_lca\_activity": "use\_phase",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "1f5f2bad-b1e2-473e-a3a8-1f7a044d01cf",  
                "replaced\_in": "25"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "1f5f2bad-b1e2-473e-a3a8-1f7a044d01cf",  
                "replaced\_in": "25.25"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",  
            "id": "e26006b4-4a78-4f4c-8f77-55debb0e851a",  
            "name": "Passenger car",  
            "category": "Vehicles",  
            "sector": "Transport",  
            "source": "EPA",  
            "scopes": \[  
                "3.4",  
                "3.6",  
                "3.7",  
                "3.9"  
            \],  
            "source\_link": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",  
            "source\_dataset": "GHG Emission Factors Hub",  
            "uncertainty": null,  
            "year": 2024,  
            "year\_released": 2024,  
            "region": "US",  
            "region\_name": "United States of America (the)",  
            "description": "Emission intensity of passenger car. Includes passenger cars/minivans/SUVs/small pickup trucks (vehicles with wheelbase less than 121 inches). Retrieved from the 2024 GHG Emission Factors Hub (xlsx) file published by the US EPA at the source URL.",  
            "unit\_type": "Distance",  
            "unit": "kg/mile",  
            "source\_lca\_activity": "use\_phase",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "8808d446-cfa5-431f-a0b1-0437624ebf2c",  
                "replaced\_in": "25"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "8808d446-cfa5-431f-a0b1-0437624ebf2c",  
                "replaced\_in": "25.25"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_fcev-distance\_na-engine\_size\_na",  
            "id": "018a7fd6-92d4-4457-b255-c27e9d10f636",  
            "name": "Hydrogen passenger car",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={3234C6FC-8626-4B4C-8B04-C3A2FEF81D2D}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of hydrogen passenger car medium. Upstream and fuel combustion LCA activity is included.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "upstream-fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "up\_to\_date"  
            },  
            "data\_version\_information": {  
                "status": "up\_to\_date"  
            }  
        },  
        {  
            "activity\_id": "passenger\_ferry-route\_type\_car\_passenger-fuel\_source\_na",  
            "id": "e6d354ab-cea4-4885-a460-675fbe28f122",  
            "name": "Ferry (passenger with car)",  
            "category": "Sea Travel",  
            "sector": "Transport",  
            "source": "BEIS",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2021",  
            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",  
            "uncertainty": null,  
            "year": 2021,  
            "year\_released": 2021,  
            "region": "GB",  
            "region\_name": "United Kingdom",  
            "description": "Emission intensity per passenger with a car on a ferry (fuel combustion only). Retrieved from the Conversion Factors 2021: flat file published by the UK BEIS/Defra at the source URL.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "f09b0fc9-6365-4683-aebd-3b2dbce9cc58",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "f09b0fc9-6365-4683-aebd-3b2dbce9cc58",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "passenger\_ferry-route\_type\_car\_passenger-fuel\_source\_na",  
            "id": "9496039d-f752-43e2-a0e8-47a952f778a8",  
            "name": "Ferry (passenger with car)",  
            "category": "Sea Travel",  
            "sector": "Transport",  
            "source": "BEIS",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024",  
            "source\_dataset": "Greenhouse gas reporting: conversion factors 2024",  
            "uncertainty": null,  
            "year": 2024,  
            "year\_released": 2024,  
            "region": "GB",  
            "region\_name": "United Kingdom",  
            "description": "Emission intensity per passenger with a car on a ferry (fuel combustion only). Retrieved from the Conversion Factors 2024: flat file published by the UK BEIS/Defra at the source URL.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "328f9966-3bd0-4d95-8fae-397e9dfa4a63",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "328f9966-3bd0-4d95-8fae-397e9dfa4a63",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "passenger\_ferry-route\_type\_car\_passenger-fuel\_source\_na",  
            "id": "44dd71ca-51fb-467a-9585-188094e37430",  
            "name": "Ferry (passenger with car)",  
            "category": "Sea Travel",  
            "sector": "Transport",  
            "source": "BEIS",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023",  
            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",  
            "uncertainty": null,  
            "year": 2023,  
            "year\_released": 2023,  
            "region": "GB",  
            "region\_name": "United Kingdom",  
            "description": "Emission intensity per passenger with a car on a ferry (fuel combustion only). Retrieved from the Conversion Factors 2023: flat file published by the UK BEIS/Defra at the source URL.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "0728ea5f-a188-4483-a01f-b890b53817d7",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "0728ea5f-a188-4483-a01f-b890b53817d7",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "passenger\_ferry-route\_type\_car\_passenger-fuel\_source\_na",  
            "id": "34822a0f-4667-4754-a709-56685d24b52b",  
            "name": "Ferry (passenger with car)",  
            "category": "Sea Travel",  
            "sector": "Transport",  
            "source": "BEIS",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2022",  
            "source\_dataset": "Greenhouse gas reporting: conversion factors 2022",  
            "uncertainty": null,  
            "year": 2022,  
            "year\_released": 2022,  
            "region": "GB",  
            "region\_name": "United Kingdom",  
            "description": "Emission intensity per passenger with a car on a ferry (fuel combustion only). Retrieved from the Conversion Factors 2022: flat file published by the UK BEIS/Defra at the source URL.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "4175d2d0-423e-4c71-ab33-3a1db4c8e764",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "4175d2d0-423e-4c71-ab33-3a1db4c8e764",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_petrol-distance\_na-engine\_size\_large",  
            "id": "5507a7c8-7eff-4334-a657-0ce28f0dcca3",  
            "name": "Petrol passenger car large",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={4BF3BE4E-88D1-4FDD-B73D-01E16F9F9DE3}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of petrol passenger car large. Emissions from fuel combustion only.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "7addcaa8-0689-453c-8bfa-4a18a9e4a8f6",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "7addcaa8-0689-453c-8bfa-4a18a9e4a8f6",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_cng-distance\_na-engine\_size\_small",  
            "id": "892069c4-0d47-4a33-afbb-359058df270e",  
            "name": "CNG passenger car small",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={FC94F44C-AFAE-4E61-B27B-DD4AFA817122}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of CNG passenger car small. Emissions from fuel combustion only.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "e8312a54-b84a-43eb-aa86-106d3c183920",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "e8312a54-b84a-43eb-aa86-106d3c183920",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_cng-distance\_na-engine\_size\_large",  
            "id": "f5eaa353-340a-41fe-82b7-3a33cb8a3dd6",  
            "name": "CNG passenger car large",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={1EF4800C-61E6-49DA-9EEF-82502633FF6E}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of CNG passenger car large. Emissions from fuel combustion only.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "f2bcca3a-5dfa-4eb6-ab69-e01e80de1cf4",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "f2bcca3a-5dfa-4eb6-ab69-e01e80de1cf4",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_bio\_petrol-distance\_na-engine\_size\_small",  
            "id": "fe065081-89d4-4b3f-a792-3e139a2710c1",  
            "name": "Petrol passenger car small",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={DABC03E2-EC5D-4437-906D-42DD91689930}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of petrol passenger car small. Emissions from fuel combustion only.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "79592863-fbc7-4b59-bd4e-c986fb7b2184",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "79592863-fbc7-4b59-bd4e-c986fb7b2184",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_bio\_petrol-distance\_na-engine\_size\_medium",  
            "id": "9e3e1d32-9158-44fa-967b-01dd4eded999",  
            "name": "Petrol passenger car medium",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={56740D43-276B-491E-8B91-A7C696112038}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of petrol passenger car medium. Emissions from fuel combustion only.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "e66d7a3e-6ffd-4f91-8305-87b103d12207",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "e66d7a3e-6ffd-4f91-8305-87b103d12207",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",  
            "id": "29a4aea2-b9ac-41a8-b382-7a8c9834eed8",  
            "name": "Passenger car",  
            "category": "Vehicles",  
            "sector": "Transport",  
            "source": "GHG Protocol",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://ghgprotocol.org/sites/default/files/GHG%20Emissions%20Calculation%20Tool\_0.xlsx",  
            "source\_dataset": "GHG Emissions Calculation Tool",  
            "uncertainty": null,  
            "year": 2021,  
            "year\_released": 2021,  
            "region": "US",  
            "region\_name": "United States of America (the)",  
            "description": "Emission intensity of passenger car. The primary source is EPA Emission Factors for Greenhouse Gas Inventories \- Table 8 Business Travel and Employee Commuting \- March 9 2018\. NOTE: This dataset has been deprecated by the source.",  
            "unit\_type": "Distance",  
            "unit": "kg/mile",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[  
                "notable\_methodological\_variance"  
            \],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "048e166a-71d1-4a47-bd5e-8428b027f288",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "048e166a-71d1-4a47-bd5e-8428b027f288",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_fcev-distance\_na-engine\_size\_small",  
            "id": "fd41d5e9-808a-42b5-b239-7304591f56e6",  
            "name": "Hydrogen passenger car small",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={AA2230CD-0099-4BB9-BD7A-90E1268A61A5}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of hydrogen passenger car small. Upstream and fuel combustion LCA activity is included.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "upstream-fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "2589b2ca-8672-44cb-b6da-9d2adced1aac",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "2589b2ca-8672-44cb-b6da-9d2adced1aac",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_fcev-distance\_na-engine\_size\_large",  
            "id": "5b72beb1-dff5-4b1a-811f-1590d8105abb",  
            "name": "Hydrogen passenger car large",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={507DB5C1-12B4-49F5-B73A-538CAC477EAB}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of hydrogen passenger car large. Upstream and fuel combustion LCA activity is included.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "upstream-fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "446d10af-f195-4d2f-a328-c04f1574b6f5",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "446d10af-f195-4d2f-a328-c04f1574b6f5",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_diesel-distance\_na-engine\_size\_small",  
            "id": "85de486d-3929-41c1-8067-5a814c961d5e",  
            "name": "Diesel passenger car small",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={8E2799FC-CFD0-4070-96FF-5CC58CF0D5E2}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of diesel passenger car small. Upstream and fuel combustion LCA activity is included.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "upstream-fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "78dad3d7-6a43-4ab3-8f55-c31fbbce76f2",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "78dad3d7-6a43-4ab3-8f55-c31fbbce76f2",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_diesel-distance\_na-engine\_size\_medium",  
            "id": "12c5a0eb-dbff-40b7-8e72-daf2ab7c3b55",  
            "name": "Diesel passenger car medium",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={8B2BD122-F6B8-432F-A348-AE1D3FF80772}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of diesel passenger car medium. Upstream and fuel combustion LCA activity is included.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "upstream-fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "b0e84c8b-2d62-4fd2-b01f-3ad951de0035",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "b0e84c8b-2d62-4fd2-b01f-3ad951de0035",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_car-fuel\_source\_diesel-distance\_na-engine\_size\_large",  
            "id": "29bcd53b-d82b-4de0-ab25-82b494e81b2e",  
            "name": "Diesel passenger car large",  
            "category": "Road Travel",  
            "sector": "Transport",  
            "source": "UBA",  
            "scopes": \[  
                "3.6",  
                "3.7"  
            \],  
            "source\_link": "https://www.probas.umweltbundesamt.de/php/prozessdetails.php?id={E1DD63C6-D2F5-4BA3-9EB5-F1F0CB0BA734}",  
            "source\_dataset": "ProBas",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2020,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of diesel passenger car large. Upstream and fuel combustion LCA activity is included.",  
            "unit\_type": "PassengerOverDistance",  
            "unit": "kg/passenger-km",  
            "source\_lca\_activity": "upstream-fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "e91ff72d-8b0f-40c9-ac1f-c97b4c2f084a",  
                "replaced\_in": "24"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "e91ff72d-8b0f-40c9-ac1f-c97b4c2f084a",  
                "replaced\_in": "24.24"  
            }  
        },  
        {  
            "activity\_id": "passenger\_vehicle-vehicle\_type\_passenger\_cars-fuel\_source\_na-engine\_size\_na-vehicle\_age\_na-vehicle\_weight\_na",  
            "id": "e00715f7-0bce-4967-a1d0-3562b8b9bfb8",  
            "name": "Passenger cars",  
            "category": "Vehicles",  
            "sector": "Transport",  
            "source": "OpenIO-Canada",  
            "scopes": \[  
                "3.2"  
            \],  
            "source\_link": "https://zenodo.org/records/10971810",  
            "source\_dataset": "OpenIO v2.9",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2024,  
            "region": "CA-NB",  
            "region\_name": "New Brunswick, CA",  
            "description": "Emission intensity of the supply chain per Canadian dollar spent on: passenger cars. Retrieved from the OpenIO-Canada v2.9 model which is a Canadian Environmentally Extended Input-Output (EEIO) model. The emission factor is provided in purchaser price including taxes retail margins and distribution costs. Endogenization is not included meaning the emission factor does not account for capital goods.",  
            "unit\_type": "Money",  
            "unit": "kg/cad",  
            "source\_lca\_activity": "cradle\_to\_gate",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "up\_to\_date"  
            },  
            "data\_version\_information": {  
                "status": "up\_to\_date"  
            }  
        }  
    \],  
    "possible\_filters": {  
        "year": \[  
            2024,  
            2023,  
            2022,  
            2021,  
            2020,  
            2019  
        \],  
        "source": \[  
            {  
                "source": "ADEME",  
                "datasets": \[  
                    "Base Carbone V21.0"  
                \]  
            },  
            {  
                "source": "BEIS",  
                "datasets": \[  
                    "Greenhouse gas reporting: conversion factors 2021",  
                    "Greenhouse gas reporting: conversion factors 2022",  
                    "Greenhouse gas reporting: conversion factors 2023",  
                    "Greenhouse gas reporting: conversion factors 2024"  
                \]  
            },  
            {  
                "source": "DISER",  
                "datasets": \[  
                    "National Greenhouse and Energy Reporting (Measurement) Determination (NGER)"  
                \]  
            },  
            {  
                "source": "EPA",  
                "datasets": \[  
                    "GHG Emission Factors Hub",  
                    "Supply Chain Greenhouse Gas Emission Factors v1.2",  
                    "Supply Chain Greenhouse Gas Emission Factors v1.3"  
                \]  
            },  
            {  
                "source": "GHG Protocol",  
                "datasets": \[  
                    "GHG Emissions Calculation Tool"  
                \]  
            },  
            {  
                "source": "Market Economics Limited",  
                "datasets": \[  
                    "Consumption emissions modelling \- Cons EF 247 NZHES"  
                \]  
            },  
            {  
                "source": "MfE",  
                "datasets": \[  
                    "Measuring emissions: A guide for organisations",  
                    "Measuring Emissions: Detailed Guide"  
                \]  
            },  
            {  
                "source": "OpenIO-Canada",  
                "datasets": \[  
                    "OpenIO v2.9"  
                \]  
            },  
            {  
                "source": "SEFR",  
                "datasets": \[  
                    "Singapore Emission Factors for Greenhouse Gas (GHG) Reporting"  
                \]  
            },  
            {  
                "source": "UBA",  
                "datasets": \[  
                    "ProBas"  
                \]  
            }  
        \],  
        "region": \[  
            {  
                "id": "AU",  
                "name": "Australia"  
            },  
            {  
                "id": "CA-AB",  
                "name": "Alberta, CA"  
            },  
            {  
                "id": "CA-BC",  
                "name": "British Columbia, CA"  
            },  
            {  
                "id": "CA-MB",  
                "name": "Manitoba, CA"  
            },  
            {  
                "id": "CA-NB",  
                "name": "New Brunswick, CA"  
            },  
            {  
                "id": "CA-NL",  
                "name": "Newfoundland and Labrador, CA"  
            },  
            {  
                "id": "CA-NS",  
                "name": "Nova Scotia, CA"  
            },  
            {  
                "id": "CA-NT",  
                "name": "Northwest Territories, CA"  
            },  
            {  
                "id": "CA-NU",  
                "name": "Nunavut, CA"  
            },  
            {  
                "id": "CA-ON",  
                "name": "Ontario, CA"  
            },  
            {  
                "id": "CA-PE",  
                "name": "Prince Edward Island, CA"  
            },  
            {  
                "id": "CA-QC",  
                "name": "Quebec, CA"  
            },  
            {  
                "id": "CA-SK",  
                "name": "Saskatchewan, CA"  
            },  
            {  
                "id": "CA-YT",  
                "name": "Yukon, CA"  
            },  
            {  
                "id": "DE",  
                "name": "Germany"  
            },  
            {  
                "id": "FR",  
                "name": "France"  
            },  
            {  
                "id": "GB",  
                "name": "United Kingdom"  
            },  
            {  
                "id": "NZ",  
                "name": "New Zealand"  
            },  
            {  
                "id": "SG",  
                "name": "Singapore"  
            },  
            {  
                "id": "US",  
                "name": "United States of America (the)"  
            }  
        \],  
        "category": \[  
            "Fuel",  
            "Rail Travel",  
            "Road Travel",  
            "Sea Travel",  
            "Vehicles"  
        \],  
        "scope": \[  
            "1",  
            "2",  
            "3.1",  
            "3.2",  
            "3.3",  
            "3.4",  
            "3.6",  
            "3.7",  
            "3.9",  
            "outside\_of\_scopes"  
        \],  
        "sector": \[  
            "Energy",  
            "Transport"  
        \],  
        "unit\_type": \[  
            "Distance",  
            "Energy",  
            "Money",  
            "PassengerOverDistance",  
            "Volume",  
            "Weight"  
        \],  
        "source\_lca\_activity": \[  
            "biogenic\_co2\_combustion",  
            "cradle\_to\_gate",  
            "cradle\_to\_shelf",  
            "electricity\_consumption",  
            "electricity\_generation",  
            "electricity\_generation-transmission\_and\_distribution",  
            "fuel\_combustion",  
            "fuel\_upstream-fuel\_combustion",  
            "fuel\_upstream-manufacturing-fuel\_combustion",  
            "fuel\_upstream-manufacturing-use\_phase",  
            "transmission\_and\_distribution",  
            "unknown",  
            "upstream-electricity\_consumption",  
            "upstream-fuel\_combustion",  
            "upstream-manufacturing-use\_phase",  
            "use\_phase",  
            "well\_to\_tank"  
        \],  
        "access\_type": \[  
            "public"  
        \],  
        "data\_quality\_flags": \[  
            "notable\_methodological\_variance"  
        \]  
    },  
    "notices": \[\]  
}

GET Search Emission Factors by activity id  
{{BASE\_URL}}/data/v1/search?activity\_id=fuel-type\_natural\_gas-fuel\_use\_industrial\&data\_version={{DATA\_VERSION}}

Response  
{  
    "current\_page": 1,  
    "last\_page": 6,  
    "total\_results": 116,  
    "results": \[  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "48487877-b9bf-40dd-9c87-2b73601a5a86",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "26de01fd-cc20-4500-ba81-4da467c469d1",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "26de01fd-cc20-4500-ba81-4da467c469d1",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "866caf42-0c11-416f-9a57-89500551e2fe",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2016,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "32b6392a-4f9d-4798-9771-f7c0ffc31b18",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "32b6392a-4f9d-4798-9771-f7c0ffc31b18",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "0a81a509-2f0f-43ee-bbef-8efa7a04b32f",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2017,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "a1df9152-66a7-4e01-a2c3-272ec3c4397a",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "a1df9152-66a7-4e01-a2c3-272ec3c4397a",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "36f82974-53e5-428e-9f32-0a2f723bec56",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2018,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "0989455e-c640-4c81-a181-333e869a1d9d",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "0989455e-c640-4c81-a181-333e869a1d9d",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "6f8a6958-8c73-4efc-ac17-aa56d5ff0082",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2019,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "ffd6da97-c428-4de5-8ed9-fd92cdd336f7",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "ffd6da97-c428-4de5-8ed9-fd92cdd336f7",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "4a2ab257-c6aa-41d2-a544-a15ccb031679",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "b53d9a82-b564-490e-ad08-070782cf8e95",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "b53d9a82-b564-490e-ad08-070782cf8e95",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "5957057f-9117-4433-8d67-ca4d59e7f155",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2021,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "b37a6e93-684f-4ef7-9451-f586ea212180",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "b37a6e93-684f-4ef7-9451-f586ea212180",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "312eec15-9b77-4c8e-8589-f095b4650bd5",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2022,  
            "year\_released": 2024,  
            "region": "CA",  
            "region\_name": "Canada",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "6ba88c93-0186-4338-8459-a9a71c6c81d4",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "6ba88c93-0186-4338-8459-a9a71c6c81d4",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "6d4d3a74-f64c-4534-b460-e0a7eedb2a47",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "12dee8ee-dc86-4b17-bcd0-6da4d85b0ada",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "12dee8ee-dc86-4b17-bcd0-6da4d85b0ada",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "2c86edea-052b-4c5c-a4d0-43fcbfa84b8b",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2016,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "c6c35c97-8a51-4b63-bc87-f42525aeb9b7",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "c6c35c97-8a51-4b63-bc87-f42525aeb9b7",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "2bab0b3b-9f5d-46a5-aa7a-46d82a17625e",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2017,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "e6063649-25d9-4d09-ab4b-de4c2ac89bf7",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "e6063649-25d9-4d09-ab4b-de4c2ac89bf7",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "c706df63-cf2f-4232-b2b2-27941a86d08d",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2018,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "b286304f-2e44-478c-8236-c0f7b6cb7d1b",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "b286304f-2e44-478c-8236-c0f7b6cb7d1b",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "9f80a1a4-ffc3-4d9d-b254-6fca305a8de7",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2019,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "fb49116a-cb4b-4c38-8339-ea3f0f38a704",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "fb49116a-cb4b-4c38-8339-ea3f0f38a704",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "6b81cba0-e4ea-46f4-8cff-419b6cbb1bfb",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2020,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "d9975d14-d8cc-440c-874b-fe5f4183233c",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "d9975d14-d8cc-440c-874b-fe5f4183233c",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "ba75d7de-09fa-43b4-99ef-95050ac32fc0",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2021,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "17c8606e-6c5c-4d57-b79f-a5f578779d13",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "17c8606e-6c5c-4d57-b79f-a5f578779d13",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "e4995815-330f-41c2-aa97-6cb6e682ed3a",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2022,  
            "year\_released": 2024,  
            "region": "CA-AB",  
            "region\_name": "Alberta, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "7deaa9ab-5058-43b1-84df-41c53f000e70",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "7deaa9ab-5058-43b1-84df-41c53f000e70",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "903ec06d-4b63-413d-82e7-c3ab4b0f5fe4",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2024,  
            "region": "CA-BC",  
            "region\_name": "British Columbia, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "db19b4f4-c8fd-4721-b043-36f04cf06115",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "db19b4f4-c8fd-4721-b043-36f04cf06115",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "f065b988-1a38-4d3c-8d0f-02d297e51f91",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2016,  
            "year\_released": 2024,  
            "region": "CA-BC",  
            "region\_name": "British Columbia, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "3056b666-b60d-4ea3-b452-1c277bb2d72f",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "3056b666-b60d-4ea3-b452-1c277bb2d72f",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "432dc8b1-48bf-4e3a-b861-f17d6f410125",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2017,  
            "year\_released": 2024,  
            "region": "CA-BC",  
            "region\_name": "British Columbia, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "a9b85c37-80c7-4086-99a9-f19e4671967f",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "a9b85c37-80c7-4086-99a9-f19e4671967f",  
                "replaced\_in": "23.23"  
            }  
        },  
        {  
            "activity\_id": "fuel-type\_natural\_gas-fuel\_use\_industrial",  
            "id": "67f3478f-dd8a-4035-b6d6-55ab31e4aba2",  
            "name": "Natural gas (industrial subsector)",  
            "category": "Fuel",  
            "sector": "Energy",  
            "source": "Government of Canada",  
            "scopes": \[  
                "1"  
            \],  
            "source\_link": "https://data-donnees.az.ec.gc.ca/data/substances/monitor/canada-s-official-greenhouse-gas-inventory/D-Emission-Factors/?lang=en",  
            "source\_dataset": "National Inventory Report",  
            "uncertainty": null,  
            "year": 2018,  
            "year\_released": 2024,  
            "region": "CA-BC",  
            "region\_name": "British Columbia, CA",  
            "description": "Emission intensity of natural gas (marketable) consumed by industrial subsector. Published in Canada 2024 National Inventory Report (NIR) \- tables A6.1-1 and A6.1-3.",  
            "unit\_type": "Volume",  
            "unit": "kg/m3",  
            "source\_lca\_activity": "fuel\_combustion",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "a2a83e07-5210-4f2b-8f9c-1c2bff8df430",  
                "replaced\_in": "23"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "a2a83e07-5210-4f2b-8f9c-1c2bff8df430",  
                "replaced\_in": "23.23"  
            }  
        }  
    \],  
    "possible\_filters": {  
        "year": \[  
            2024,  
            2023,  
            2022,  
            2021,  
            2020,  
            2019,  
            2018,  
            2017,  
            2016,  
            2015  
        \],  
        "source": \[  
            {  
                "source": "Government of Canada",  
                "datasets": \[  
                    "National Inventory Report"  
                \]  
            },  
            {  
                "source": "MfE",  
                "datasets": \[  
                    "Measuring emissions: A guide for organisations"  
                \]  
            }  
        \],  
        "region": \[  
            {  
                "id": "CA",  
                "name": "Canada"  
            },  
            {  
                "id": "CA-AB",  
                "name": "Alberta, CA"  
            },  
            {  
                "id": "CA-BC",  
                "name": "British Columbia, CA"  
            },  
            {  
                "id": "CA-MB",  
                "name": "Manitoba, CA"  
            },  
            {  
                "id": "CA-NB",  
                "name": "New Brunswick, CA"  
            },  
            {  
                "id": "CA-NL",  
                "name": "Newfoundland and Labrador, CA"  
            },  
            {  
                "id": "CA-NS",  
                "name": "Nova Scotia, CA"  
            },  
            {  
                "id": "CA-NT",  
                "name": "Northwest Territories, CA"  
            },  
            {  
                "id": "CA-NU",  
                "name": "Nunavut, CA"  
            },  
            {  
                "id": "CA-ON",  
                "name": "Ontario, CA"  
            },  
            {  
                "id": "CA-PE",  
                "name": "Prince Edward Island, CA"  
            },  
            {  
                "id": "CA-QC",  
                "name": "Quebec, CA"  
            },  
            {  
                "id": "CA-SK",  
                "name": "Saskatchewan, CA"  
            },  
            {  
                "id": "CA-YT",  
                "name": "Yukon, CA"  
            },  
            {  
                "id": "NZ",  
                "name": "New Zealand"  
            }  
        \],  
        "category": \[  
            "Fuel"  
        \],  
        "scope": \[  
            "1"  
        \],  
        "sector": \[  
            "Energy"  
        \],  
        "unit\_type": \[  
            "Energy",  
            "Volume"  
        \],  
        "source\_lca\_activity": \[  
            "fuel\_combustion"  
        \],  
        "access\_type": \[  
            "public"  
        \],  
        "data\_quality\_flags": \[\]  
    },  
    "notices": \[\]  
}

GET Search Emission Factors with filters  
{{BASE\_URL}}/data/v1/search?sector=Energy\&data\_version={{DATA\_VERSION}}\&year=2015\&category=Electricity\&source=GEMIS\&region=DE\&unit\_type=Energy\&source\_lca\_activity=upstream-use\_phase-transport\&calculation\_method=ar4\&allowed\_data\_quality\_flags=none\&access\_type=public\&page=2\&results\_per\_page=5

Response  
{  
    "current\_page": 2,  
    "last\_page": 4,  
    "total\_results": 19,  
    "results": \[  
        {  
            "activity\_id": "electricity-supply\_grid-source\_hydro\_10\_mw",  
            "id": "d6fc5770-5e93-4277-a1ad-5c308c51b50e",  
            "name": "Electricity supplied from hydro power plant 10 MW",  
            "category": "Electricity",  
            "sector": "Energy",  
            "source": "GEMIS",  
            "scopes": \[  
                "combined\_scopes"  
            \],  
            "source\_link": "https://iinas.org/downloads/gemis-downloads/",  
            "source\_dataset": "GEMIS model and database v5.0",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2021,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of large run-of-river power plant located in Germany. Total life cycle incl. transport \+ material input without disposal. Retrieved from GEMIS v5.0.",  
            "unit\_type": "Energy",  
            "unit": "kg/kWh",  
            "source\_lca\_activity": "upstream-use\_phase-transport",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "up\_to\_date"  
            },  
            "data\_version\_information": {  
                "status": "up\_to\_date"  
            }  
        },  
        {  
            "activity\_id": "electricity-supply\_grid-source\_imported\_coal",  
            "id": "587fd98d-c958-41f1-af21-26d943b8f53d",  
            "name": "Electricity supplied from grid coal-fired power plant (imported coal)",  
            "category": "Electricity",  
            "sector": "Energy",  
            "source": "GEMIS",  
            "scopes": \[  
                "combined\_scopes"  
            \],  
            "source\_link": "https://iinas.org/downloads/gemis-downloads/",  
            "source\_dataset": "GEMIS model and database v5.0",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2021,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of large hard-coal-fired power plant for imported coal mix. Free grid feed-in. Total life cycle incl. transport \+ material input without disposal. Retrieved from GEMIS v5.0.",  
            "unit\_type": "Energy",  
            "unit": "kg/kWh",  
            "source\_lca\_activity": "upstream-use\_phase-transport",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "d5cc099f-0b92-419d-b4ae-8f11c020b50c",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "d5cc099f-0b92-419d-b4ae-8f11c020b50c",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "electricity-supply\_grid-source\_landfill\_gas",  
            "id": "92abe2f4-e9aa-4afb-a70e-689242301d5b",  
            "name": "Electricity supplied from landfill gas",  
            "category": "Electricity",  
            "sector": "Energy",  
            "source": "GEMIS",  
            "scopes": \[  
                "combined\_scopes"  
            \],  
            "source\_link": "https://iinas.org/downloads/gemis-downloads/",  
            "source\_dataset": "GEMIS model and database v5.0",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2021,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of gas engine with 1 MW electric for landfill gas (without heat utilization). Total life cycle incl. transport \+ material input without disposal. Retrieved from GEMIS v5.0.",  
            "unit\_type": "Energy",  
            "unit": "kg/kWh",  
            "source\_lca\_activity": "upstream-use\_phase-transport",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "7d698628-523e-429c-add7-1eb7ca125f52",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "7d698628-523e-429c-add7-1eb7ca125f52",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "electricity-supply\_grid-source\_lignite",  
            "id": "331a588c-fe7f-47b1-b9a4-1ce9b1d85be4",  
            "name": "Electricity supplied from lignite-fired power plant",  
            "category": "Electricity",  
            "sector": "Energy",  
            "source": "GEMIS",  
            "scopes": \[  
                "combined\_scopes"  
            \],  
            "source\_link": "https://iinas.org/downloads/gemis-downloads/",  
            "source\_dataset": "GEMIS model and database v5.0",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2021,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of large lignite-fired power plant (rhenish). Free grid feed-in. Total life cycle incl. transport \+ material input without disposal. Retrieved from GEMIS v5.0.",  
            "unit\_type": "Energy",  
            "unit": "kg/kWh",  
            "source\_lca\_activity": "upstream-use\_phase-transport",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "b50dc74f-4565-425f-80f8-17c4865f43fa",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "b50dc74f-4565-425f-80f8-17c4865f43fa",  
                "replaced\_in": "28.28"  
            }  
        },  
        {  
            "activity\_id": "electricity-supply\_grid-source\_natural\_gas\_ccgt",  
            "id": "a772c1f0-0597-41b5-b154-387186b14eae",  
            "name": "Electricity supplied from natural gas CCGT power plant",  
            "category": "Electricity",  
            "sector": "Energy",  
            "source": "GEMIS",  
            "scopes": \[  
                "combined\_scopes"  
            \],  
            "source\_link": "https://iinas.org/downloads/gemis-downloads/",  
            "source\_dataset": "GEMIS model and database v5.0",  
            "uncertainty": null,  
            "year": 2015,  
            "year\_released": 2021,  
            "region": "DE",  
            "region\_name": "Germany",  
            "description": "Emission intensity of large natural gas power plant with gas and steam turbine (combined cycle). Free grid feed-in. Total life cycle incl. transport \+ material input without disposal. Retrieved from GEMIS v5.0.",  
            "unit\_type": "Energy",  
            "unit": "kg/kWh",  
            "source\_lca\_activity": "upstream-use\_phase-transport",  
            "data\_quality\_flags": \[\],  
            "access\_type": "public",  
            "supported\_calculation\_methods": \[  
                "ar4",  
                "ar5",  
                "ar6"  
            \],  
            "factor": null,  
            "factor\_calculation\_method": null,  
            "factor\_calculation\_origin": null,  
            "constituent\_gases": {  
                "co2e\_total": null,  
                "co2e\_other": null,  
                "co2": null,  
                "ch4": null,  
                "n2o": null  
            },  
            "data\_version": {  
                "status": "replaced",  
                "replaced\_by": "a5c6a51e-c002-47a3-9ff2-d1e8d8bcf83f",  
                "replaced\_in": "28"  
            },  
            "data\_version\_information": {  
                "status": "replaced",  
                "replaced\_by": "a5c6a51e-c002-47a3-9ff2-d1e8d8bcf83f",  
                "replaced\_in": "28.28"  
            }  
        }  
    \],  
    "possible\_filters": {  
        "year": \[  
            2015  
        \],  
        "source": \[  
            {  
                "source": "GEMIS",  
                "datasets": \[  
                    "GEMIS model and database v5.0"  
                \]  
            }  
        \],  
        "region": \[  
            {  
                "id": "DE",  
                "name": "Germany"  
            }  
        \],  
        "category": \[  
            "Electricity"  
        \],  
        "scope": \[  
            "2",  
            "3.3"  
        \],  
        "sector": \[  
            "Energy"  
        \],  
        "unit\_type": \[  
            "Energy"  
        \],  
        "source\_lca\_activity": \[  
            "upstream-use\_phase-transport"  
        \],  
        "access\_type": \[  
            "public"  
        \],  
        "data\_quality\_flags": \[\]  
    },  
    "notices": \[\]  
}

GET all unit types  
{{BASE\_URL}}/data/v1/unit-types  
Response  
{  
    "unit\_types": \[  
        {  
            "unit\_type": "Area",  
            "units": {  
                "area\_unit": \[  
                    "m2",  
                    "km2",  
                    "ft2",  
                    "ha"  
                \]  
            }  
        },  
        {  
            "unit\_type": "AreaOverTime",  
            "units": {  
                "area\_unit": \[  
                    "m2",  
                    "km2",  
                    "ft2",  
                    "ha"  
                \],  
                "time\_unit": \[  
                    "ms",  
                    "s",  
                    "min",  
                    "hour",  
                    "day",  
                    "year"  
                \]  
            }  
        },  
        {  
            "unit\_type": "ContainerOverDistance",  
            "units": {  
                "distance\_unit": \[  
                    "m",  
                    "km",  
                    "ft",  
                    "mi",  
                    "nmi"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Data",  
            "units": {  
                "data\_unit": \[  
                    "MB",  
                    "GB",  
                    "TB"  
                \]  
            }  
        },  
        {  
            "unit\_type": "DataOverTime",  
            "units": {  
                "data\_unit": \[  
                    "MB",  
                    "GB",  
                    "TB"  
                \],  
                "time\_unit": \[  
                    "ms",  
                    "s",  
                    "min",  
                    "hour",  
                    "day",  
                    "year"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Distance",  
            "units": {  
                "distance\_unit": \[  
                    "m",  
                    "km",  
                    "ft",  
                    "mi",  
                    "nmi"  
                \]  
            }  
        },  
        {  
            "unit\_type": "DistanceOverTime",  
            "units": {  
                "distance\_unit": \[  
                    "m",  
                    "km",  
                    "ft",  
                    "mi",  
                    "nmi"  
                \],  
                "time\_unit": \[  
                    "ms",  
                    "s",  
                    "min",  
                    "hour",  
                    "day",  
                    "year"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Energy",  
            "units": {  
                "energy\_unit": \[  
                    "Wh",  
                    "kWh",  
                    "MWh",  
                    "MJ",  
                    "GJ",  
                    "TJ",  
                    "BTU",  
                    "therm",  
                    "MMBTU"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Money",  
            "units": {  
                "money\_unit": \[  
                    "aed",  
                    "afn",  
                    "all",  
                    "amd",  
                    "ang",  
                    "aoa",  
                    "ars",  
                    "aud",  
                    "awg",  
                    "azn",  
                    "bam",  
                    "bbd",  
                    "bdt",  
                    "bgn",  
                    "bhd",  
                    "bif",  
                    "bmd",  
                    "bnd",  
                    "bob",  
                    "brl",  
                    "bsd",  
                    "bwp",  
                    "byn",  
                    "cad",  
                    "chf",  
                    "clp",  
                    "cny",  
                    "cop",  
                    "crc",  
                    "cve",  
                    "czk",  
                    "djf",  
                    "dkk",  
                    "dop",  
                    "dzd",  
                    "egp",  
                    "etb",  
                    "eur",  
                    "fjd",  
                    "gbp",  
                    "gel",  
                    "ghs",  
                    "gip",  
                    "gmd",  
                    "gtq",  
                    "gyd",  
                    "hkd",  
                    "hnl",  
                    "huf",  
                    "idr",  
                    "ils",  
                    "inr",  
                    "iqd",  
                    "irr",  
                    "isk",  
                    "jmd",  
                    "jod",  
                    "jpy",  
                    "kes",  
                    "kgs",  
                    "khr",  
                    "kmf",  
                    "krw",  
                    "kwd",  
                    "kyd",  
                    "kzt",  
                    "lak",  
                    "lbp",  
                    "lsl",  
                    "lyd",  
                    "mad",  
                    "mdl",  
                    "mga",  
                    "mkd",  
                    "mop",  
                    "mur",  
                    "mvr",  
                    "mxn",  
                    "myr",  
                    "mzn",  
                    "nad",  
                    "nio",  
                    "nok",  
                    "npr",  
                    "nzd",  
                    "omr",  
                    "pab",  
                    "pen",  
                    "php",  
                    "pkr",  
                    "pln",  
                    "pyg",  
                    "qar",  
                    "ron",  
                    "rsd",  
                    "rub",  
                    "rwf",  
                    "sar",  
                    "scr",  
                    "sek",  
                    "sgd",  
                    "sle",  
                    "srd",  
                    "std",  
                    "szl",  
                    "thb",  
                    "tjs",  
                    "tnd",  
                    "try",  
                    "ttd",  
                    "twd",  
                    "uah",  
                    "ugx",  
                    "usd",  
                    "uyu",  
                    "uzs",  
                    "vnd",  
                    "wst",  
                    "xaf",  
                    "xcd",  
                    "xof",  
                    "xpf",  
                    "yer",  
                    "zar",  
                    "zmw"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Number",  
            "units": {}  
        },  
        {  
            "unit\_type": "NumberOverTime",  
            "units": {  
                "time\_unit": \[  
                    "ms",  
                    "s",  
                    "min",  
                    "hour",  
                    "day",  
                    "year"  
                \]  
            }  
        },  
        {  
            "unit\_type": "PassengerOverDistance",  
            "units": {  
                "distance\_unit": \[  
                    "m",  
                    "km",  
                    "ft",  
                    "mi",  
                    "nmi"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Power",  
            "units": {  
                "power\_unit": \[  
                    "W",  
                    "kW",  
                    "MW"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Time",  
            "units": {  
                "time\_unit": \[  
                    "ms",  
                    "s",  
                    "min",  
                    "hour",  
                    "day",  
                    "year"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Volume",  
            "units": {  
                "volume\_unit": \[  
                    "ml",  
                    "l",  
                    "m3",  
                    "cubic\_foot",  
                    "gallon\_us",  
                    "bbl"  
                \]  
            }  
        },  
        {  
            "unit\_type": "Weight",  
            "units": {  
                "weight\_unit": \[  
                    "g",  
                    "kg",  
                    "t",  
                    "ton",  
                    "lb"  
                \]  
            }  
        },  
        {  
            "unit\_type": "WeightOverDistance",  
            "units": {  
                "distance\_unit": \[  
                    "m",  
                    "km",  
                    "ft",  
                    "mi",  
                    "nmi"  
                \],  
                "weight\_unit": \[  
                    "g",  
                    "kg",  
                    "t",  
                    "ton",  
                    "lb"  
                \]  
            }  
        },  
        {  
            "unit\_type": "WeightOverTime",  
            "units": {  
                "time\_unit": \[  
                    "ms",  
                    "s",  
                    "min",  
                    "hour",  
                    "day",  
                    "year"  
                \],  
                "weight\_unit": \[  
                    "g",  
                    "kg",  
                    "t",  
                    "ton",  
                    "lb"  
                \]  
            }  
        }  
    \]  
}

GET data versions  
{{BASE\_URL}}/data/v1/data-version  
Response  
{  
    "latest\_release": "29",  
    "latest": "29.29",  
    "latest\_major": 29,  
    "latest\_minor": 29  
}

## **Freight Flights**

Calculate total estimated emissions produced by freight transport

* Road  
* Sea  
* Air  
* Rail

{{BASE\_URL}}/freight/v2/intermodal

POST Road

{

    "route": \[

        {

            "location": {

                "query": "Hamburg"

            }

        },

        {

            "transport\_mode": "road",

            "leg\_details": {

                "rest\_of\_world": {

                    "vehicle\_type": "van",

                    "vehicle\_weight": "lte\_3.5t",

                    "fuel\_source": "petrol"

                },

                "north\_america": {

                    "vehicle\_type": "moving"

                }

            }

        },

        {

            "location": {

                "query": "Berlin"

            }

        }

    \],

    "cargo": {

        "weight": 10,

        "weight\_unit": "t"

    }

}

Response

{

    "co2e": 2792.3789,

    "hub\_equipment\_co2e": 12.0,

    "vehicle\_operation\_co2e": 2106.78195,

    "vehicle\_energy\_provision\_co2e": 673.59695,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

    "cargo\_tonnes": 10.0,

    "distance\_km": 286.637,

    "route": \[

        {

            "type": "location",

            "co2e": 6.0,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- transshipment \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "7df9317a-1360-4f23-a5b9-923b1fe4a360"

                }

            \],

            "name": "Hamburg, Germany",

            "confidence\_score": 1.0

        },

        {

            "type": "leg",

            "co2e": 2780.3789,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Van \<3.5t \- Petrol",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "EU\_S\_AMERICA",

                    "region\_name": "Europe and South America",

                    "id": "95523be3-9efc-4e4e-8046-24dc2026ff09"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Van \<3.5t \- Petrol",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "EU\_S\_AMERICA",

                    "region\_name": "Europe and South America",

                    "id": "ceda8413-b781-47d4-8bf1-5351dd398351"

                }

            \],

            "vehicle\_operation\_co2e": 2106.78195,

            "vehicle\_energy\_provision\_co2e": 673.59695,

            "transport\_mode": "road",

            "distance\_km": 286.637,

            "notices": \[\]

        },

        {

            "type": "location",

            "co2e": 6.0,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- transshipment \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "7df9317a-1360-4f23-a5b9-923b1fe4a360"

                }

            \],

            "name": "Berlin, Germany",

            "confidence\_score": 1.0

        }

    \]

}

POST Sea

{

    "route": \[

        {

            "location": {

                "query": "Hamburg"

            }

        },

        {

            "transport\_mode": "sea",

            "leg\_details": {

                "vessel\_type": "container\_reefer\_refrigerated"

            }

        },

        {

            "location": {

                "query": "London"

            }

        }

    \],

    "cargo": {

        "weight": 10,

        "weight\_unit": "t"

    }

}

Response

{

    "co2e": 258.045009128,

    "hub\_equipment\_co2e": 21.4,

    "vehicle\_operation\_co2e": 204.345945595,

    "vehicle\_energy\_provision\_co2e": 32.2990635331,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

    "cargo\_tonnes": 10.0,

    "distance\_km": 805.462931,

    "route": \[

        {

            "type": "location",

            "co2e": 10.7,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- maritime container terminals \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "2479886b-e9be-4d5a-ae53-a966a26fd2c2"

                }

            \],

            "name": "Sea Port at HAMBURG",

            "confidence\_score": 1.0

        },

        {

            "type": "leg",

            "co2e": 236.645009128,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Intra North Europe \- Container ship \- reefer (refrigerated)",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "a713e67b-0f3a-424b-a703-d584e1d4863d"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Intra North Europe \- Container ship \- reefer (refrigerated)",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "b7a0ff4d-747a-476d-b1c1-f7170f078cff"

                }

            \],

            "vehicle\_operation\_co2e": 204.345945595,

            "vehicle\_energy\_provision\_co2e": 32.2990635331,

            "transport\_mode": "sea",

            "distance\_km": 805.462931,

            "notices": \[\]

        },

        {

            "type": "location",

            "co2e": 10.7,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- maritime container terminals \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "2479886b-e9be-4d5a-ae53-a966a26fd2c2"

                }

            \],

            "name": "Sea Port at LONDON",

            "confidence\_score": 1.0

        }

    \]

}

POST Air

{

    "route": \[

        { "location": { "query": "Hamburg" } },

        {

            "transport\_mode": "air",

            "leg\_details": {

                "aircraft\_type": "freighter"

            }

        },

        { "location": { "query": "London City Airport" } }

    \],

    "cargo": {

        "weight": 10,

        "weight\_unit": "t"

    }

}

Response

{

    "co2e": 19229.945255,

    "hub\_equipment\_co2e": 12.0,

    "vehicle\_operation\_co2e": 16978.3400921,

    "vehicle\_energy\_provision\_co2e": 2239.6051629,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

    "cargo\_tonnes": 10.0,

    "distance\_km": 710.985766,

    "route": \[

        {

            "type": "location",

            "co2e": 6.0,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- transshipment \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "7df9317a-1360-4f23-a5b9-923b1fe4a360"

                }

            \],

            "name": "Hamburg Helmut Schmidt Airport",

            "confidence\_score": 1.0

        },

        {

            "type": "leg",

            "co2e": 19217.945255,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Radiative Forcing uplift",

                    "source": "The International Journal of Life Cycle Assessment",

                    "source\_dataset": "Jungbluth, N., Meili, C. Recommendations for calculation of the global warming potential of aviation including the radiative forcing index. Int J Life Cycle Assess 24, 404–411 (2019). https://doi.org/10.1007/s11367-018-1556-3",

                    "year": null,

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Air freight (\<1500 km) \- freighter \- RP1678",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "62dfe661-b75b-4a41-ad0d-7c7ce7ed27e9"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Air freight (\<1500 km) \- freighter \- RP1678",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "6994785b-aad2-4ee9-83f3-f01e47f9b6c1"

                }

            \],

            "vehicle\_operation\_co2e": 16978.3400921,

            "vehicle\_energy\_provision\_co2e": 2239.6051629,

            "transport\_mode": "air",

            "distance\_km": 710.985766,

            "notices": \[

                {

                    "message": "A Radiative Forcing Index of 2 applied to operational emissions of air leg. This value accounts for the fact that greenhouse gases emitted at higher altitudes contribute more to global warming.",

                    "code": "radiative\_forcing\_applied",

                    "severity": "info"

                }

            \]

        },

        {

            "type": "location",

            "co2e": 6.0,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- transshipment \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "7df9317a-1360-4f23-a5b9-923b1fe4a360"

                }

            \],

            "name": "London City Airport",

            "confidence\_score": 1.0

        }

    \]

}

POST Rail

{

    "route": \[

        {

            "location": {

                "query": "Hamburg"

            }

        },

        {

            "transport\_mode": "rail",

            "leg\_details": {

                "fuel\_source": "electricity"

            }

        },

        {

            "location": {

                "query": "London Victoria"

            }

        }

    \],

    "cargo": {

        "weight": 10,

        "weight\_unit": "t"

    }

}

Response

{

    "co2e": 80.5220647087,

    "hub\_equipment\_co2e": 12.0,

    "vehicle\_operation\_co2e": 0.0,

    "vehicle\_energy\_provision\_co2e": 68.5220647087,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

    "cargo\_tonnes": 10.0,

    "distance\_km": 978.886638695,

    "route": \[

        {

            "type": "location",

            "co2e": 6.0,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- transshipment \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "7df9317a-1360-4f23-a5b9-923b1fe4a360"

                }

            \],

            "name": "Hafenbahnhof Hamburg Süd",

            "confidence\_score": 1.0

        },

        {

            "type": "leg",

            "co2e": 68.5220647087,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Rail freight (electric traction) \- average/mixed load \- distribution losses",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": "fa645ba8-1b9c-4798-affd-f7a50921e950"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Rail freight (electric traction) \- average/mixed load \- operational emissions",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": "d076a9ad-b8e3-4c00-a1de-f6b4c444da64"

                }

            \],

            "vehicle\_operation\_co2e": 0.0,

            "vehicle\_energy\_provision\_co2e": 68.5220647087,

            "transport\_mode": "rail",

            "distance\_km": 978.886638695,

            "notices": \[\]

        },

        {

            "type": "location",

            "co2e": 6.0,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": "emission\_factor",

                    "name": "Freight logistics \- transshipment \- ambient",

                    "source": "GLEC",

                    "source\_dataset": "Default fuel efficiency and GHG emission intensity values v3.0",

                    "year": "2023",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "7df9317a-1360-4f23-a5b9-923b1fe4a360"

                }

            \],

            "name": "Victoria (Grosvenor) Carriage Shed",

            "confidence\_score": 1.0

        }

    \]

}

## **Procurement**

Spend-based estimations for purchased goods and services (GHG Protocol Category 3.1)  
{{BASE\_URL}}/procurement/v1/spend/batch

POST Procurement  
{  
  "activity": {  
        "classification\_code": "25",  
        "classification\_type": "isic4"  
    },  
    "spend\_year": 2022,  
    "spend\_region": "DE",  
    "money": 100,  
    "money\_unit": "eur",  
    "tax\_margin": 0.2  
}

Response

{

    "estimate": {

        "co2e": 15.6603855843,

        "co2e\_unit": "kg",

        "co2e\_calculation\_method": "ar5",

        "co2e\_calculation\_origin": "source",

        "emission\_factor": null,

        "constituent\_gases": null,

        "activity\_data": {

            "activity\_value": 61.0303413264,

            "activity\_unit": "eur"

        },

        "audit\_trail": "disabled"

    },

    "calculation\_details": null,

    "notices": \[\],

    "source\_trail": \[

        {

            "data\_category": null,

            "name": "Average trade margins for spend type",

            "source": "EXIOBASE",

            "source\_dataset": null,

            "year": null,

            "region": "DE",

            "region\_name": "Germany",

            "id": null

        },

        {

            "data\_category": null,

            "name": "Average transport margins for spend type",

            "source": "EXIOBASE",

            "source\_dataset": null,

            "year": null,

            "region": "DE",

            "region\_name": "Germany",

            "id": null

        },

        {

            "data\_category": null,

            "name": "Industry-specific inflation rates",

            "source": "EUROSTAT",

            "source\_dataset": null,

            "year": null,

            "region": "DE",

            "region\_name": "Germany",

            "id": null

        },

        {

            "data\_category": "emission\_factor",

            "name": "Fabricated metal products/except machinery and equipment",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "DE",

            "region\_name": "Germany",

            "id": "f30ce73e-6f49-46ac-8840-c0bee742164c"

        }

    \]

}

POST Procurement Batch  
\[  
    {  
        "activity": {  
            "classification\_code": "25",  
            "classification\_type": "isic4"  
        },  
        "spend\_year": 2022,  
        "spend\_region": "DE",  
        "money": 100,  
        "money\_unit": "eur",  
        "tax\_margin": 0.2  
    },  
    {  
        "activity": {  
            "classification\_code": "25",  
            "classification\_type": "isic4"  
        },  
        "spend\_year": 2020,  
        "spend\_region": "ES",  
        "money": 200,  
        "money\_unit": "eur",  
        "tax\_margin": 0.3  
    }  
\]

Response

{

    "results": \[

        {

            "estimate": {

                "co2e": 15.6603855843,

                "co2e\_unit": "kg",

                "co2e\_calculation\_method": "ar5",

                "co2e\_calculation\_origin": "source",

                "emission\_factor": null,

                "constituent\_gases": null,

                "activity\_data": {

                    "activity\_value": 61.0303413264,

                    "activity\_unit": "eur"

                },

                "audit\_trail": "disabled"

            },

            "calculation\_details": null,

            "notices": \[\],

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Average trade margins for spend type",

                    "source": "EXIOBASE",

                    "source\_dataset": null,

                    "year": null,

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Average transport margins for spend type",

                    "source": "EXIOBASE",

                    "source\_dataset": null,

                    "year": null,

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Industry-specific inflation rates",

                    "source": "EUROSTAT",

                    "source\_dataset": null,

                    "year": null,

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Fabricated metal products/except machinery and equipment",

                    "source": "EXIOBASE",

                    "source\_dataset": "EXIOBASE 3",

                    "year": "2019",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "f30ce73e-6f49-46ac-8840-c0bee742164c"

                }

            \]

        },

        {

            "estimate": {

                "co2e": 58.1013690063,

                "co2e\_unit": "kg",

                "co2e\_calculation\_method": "ar5",

                "co2e\_calculation\_origin": "source",

                "emission\_factor": null,

                "constituent\_gases": null,

                "activity\_data": {

                    "activity\_value": 123.14830226,

                    "activity\_unit": "eur"

                },

                "audit\_trail": "disabled"

            },

            "calculation\_details": null,

            "notices": \[\],

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Average trade margins for spend type",

                    "source": "EXIOBASE",

                    "source\_dataset": null,

                    "year": null,

                    "region": "ES",

                    "region\_name": "Spain",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Average transport margins for spend type",

                    "source": "EXIOBASE",

                    "source\_dataset": null,

                    "year": null,

                    "region": "ES",

                    "region\_name": "Spain",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Industry-specific inflation rates",

                    "source": "EUROSTAT",

                    "source\_dataset": null,

                    "year": null,

                    "region": "ES",

                    "region\_name": "Spain",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Fabricated metal products/except machinery and equipment",

                    "source": "EXIOBASE",

                    "source\_dataset": "EXIOBASE 3",

                    "year": "2019",

                    "region": "ES",

                    "region\_name": "Spain",

                    "id": "9f51d3f1-8d1c-48fa-accb-b8ec6dd2ecda"

                }

            \]

        }

    \]

}

## [**Classifications**](https://www.climatiq.io/docs#classifications)

Many sources link [emission factors](https://www.climatiq.io/explorer) to specific industry classification schemes, and Climatiq makes it possible to select an emission factor based on these industry classification codes. Please see below the list of mappings we currently support, with the datasets that are mapped directly to them (note that the API will also map factors indirectly via the [UN correspondence tables](https://unstats.un.org/unsd/classifications/Econ/isic)):

| INDUSTRY CLASSIFICATION CODE | PRIMARY DATASET |
| ----- | ----- |
| [**ISIC Rev. 4**](https://unstats.un.org/unsd/classifications/Econ/isic) | [**GHG Protocol**](https://www.climatiq.io/explorer?source=GHG+Protocol&unit_type=Money) **(via ISIC 3.1)** |
| [**NACE Rev. 2**](https://ec.europa.eu/eurostat/web/nace-rev2) | [**EXIOBASE3**](https://www.climatiq.io/explorer?source=EXIOBASE) |

For a more in-depth view on how Climatiq works with classification schemes, [view the classification guide](https://www.climatiq.io/docs/guides/classification-codes-intro).

## [**Estimate**](https://www.climatiq.io/docs#classifications-estimate)

Calculate total estimated emissions produced for a particular activity, as described by an industry classification scheme such as [ISIC](https://en.wikipedia.org/wiki/International_Standard_Industrial_Classification) or [NACE](https://en.wikipedia.org/wiki/Statistical_Classification_of_Economic_Activities_in_the_European_Community).

This endpoint lets you specify an industry classification code and have Climatiq automatically select the appropriate emission factor.

One industry code might be linked to more than one emission factor. If that happens, Climatiq will automatically select the most conservative emission factor. If you would like to specify exactly what emission factor to use, you can specify other attributes to filter on, such as `year`, `source` or `region`.

Industry classification codes can also be mapped to each other using the [UN correspondence tables](https://unstats.un.org/unsd/classifications/Econ/isic), allowing Climatiq to return emission factors from other classification schemes that represent the same activity if there isn't one found directly; this may happen for example because of different classification taxonomies being used in different geographies or by different data sources.

As with any estimation endpoint, the emission factor must be provided with parameters, such as weight, volume, energy. These are provided through the `parameters` field. See the [estimate endpoint](https://www.climatiq.io/docs#estimate) for more details on how parameters and units work.

{{BASE\_URL}}/classifications/v1/estimate

POST Estimate using isic4

{

    "classification": {

        "classification\_code": "25",

        "classification\_type": "isic4"

    },

    "parameters": {

        "money": 1,

        "money\_unit": "usd"

    }

}

Response

{

    "co2e": 1.9701972,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar5",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": null,

    "constituent\_gases": null,

    "activity\_data": {

        "activity\_value": 0.894,

        "activity\_unit": "eur"

    },

    "audit\_trail": "disabled",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Fabricated metal products/except machinery and equipment",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "IN",

            "region\_name": "India",

            "id": "f9682106-3615-4d90-b200-89c7b938a256"

        }

    \]

}

POST Estimate isic4 and source filter

{

    "classification": {

        "classification\_code": "25",

        "classification\_type": "isic4",

        "source": "EXIOBASE"

    },

    "parameters": {

        "money": 1,

        "money\_unit": "usd"

    }

}

Response

{

    "co2e": 1.9701972,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar5",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": null,

    "constituent\_gases": null,

    "activity\_data": {

        "activity\_value": 0.894,

        "activity\_unit": "eur"

    },

    "audit\_trail": "disabled",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Fabricated metal products/except machinery and equipment",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "IN",

            "region\_name": "India",

            "id": "f9682106-3615-4d90-b200-89c7b938a256"

        }

    \]

}

POST Estimate isic4 and region fallback

{

    "classification": {

        "classification\_code": "25",

        "classification\_type": "isic4",

        "region\_fallback": true,

        "region": "IS"

    },

    "parameters": {

        "money": 1,

        "money\_unit": "usd"

    }

}

Response

{

    "co2e": 1.128228,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar5",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": null,

    "constituent\_gases": null,

    "activity\_data": {

        "activity\_value": 0.894,

        "activity\_unit": "eur"

    },

    "audit\_trail": "disabled",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Fabricated metal products/except machinery and equipment",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "ROW\_WE",

            "region\_name": "East Europe and Iceland",

            "id": "a7268e02-0914-42c7-b940-f4b56432a3df"

        }

    \]

}

POST Estimate using nace2

{

    "classification": {

        "classification\_code": "6.2",

        "classification\_type": "nace2"

    },

    "parameters": {

        "money": 1,

        "money\_unit": "usd"

    }

}

Response

{

    "co2e": 17.7108552,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar5",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": null,

    "constituent\_gases": null,

    "activity\_data": {

        "activity\_value": 0.894,

        "activity\_unit": "eur"

    },

    "audit\_trail": "disabled",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Natural gas and services related to natural gas extraction (excluding surveying)",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "HR",

            "region\_name": "Croatia",

            "id": "ba300dae-b4ac-49a3-9709-c187700f1e00"

        }

    \]

}

POST Estimate using nace2 and region fallback

{

    "classification": {

        "classification\_code": "6.2",

        "classification\_type": "nace2"

    },

    "parameters": {

        "money": 1,

        "money\_unit": "usd"

    }

}

Response

{

    "co2e": 17.7108552,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ar5",

    "co2e\_calculation\_origin": "source",

    "emission\_factor": null,

    "constituent\_gases": null,

    "activity\_data": {

        "activity\_value": 0.894,

        "activity\_unit": "eur"

    },

    "audit\_trail": "disabled",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Natural gas and services related to natural gas extraction (excluding surveying)",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "HR",

            "region\_name": "Croatia",

            "id": "ba300dae-b4ac-49a3-9709-c187700f1e00"

        }

    \]

}

## **Custom Mappings**

Use custom mapped activities from your Climatiq Dashboard to calculate emissions.

{{BASE\_URL}}/custom-mappings/v1/estimate

 POST Estimate  
{{BASE\_URL}}/custom-mappings/v1/estimate  
{  
    "custom\_mapping": {  
        "label": "Electricity generation",  
        "data\_version":"0.0"  
    },  
    "parameters": {  
        "energy": 100,  
        "energy\_unit": "kWh"  
    }  
}

Response

POST Labels Copy

{{BASE\_URL}}/custom-mappings/v1/labels  
{  
  "data\_version": "0.0",  
  "labels": \[  
    {  
        "label": "Electricity generation",  
        "source": \["BEIS"\]  
    }  
  \]  
}

Response  
\[  
    {  
        "label": "Electricity generation",  
        "activity\_id": "electricity-energy\_source\_grid\_mix",  
        "id": "430917622085745263"  
    }  
\]

   
POST batch estimate  
{{BASE\_URL}}/custom-mappings/v1/batch

\[  
    {  
        "custom\_mapping": {  
            "label": "Electricity generation",  
            "data\_version":"0.0"  
        },  
        "parameters": {  
            "energy": 100,  
            "energy\_unit": "kWh"  
        }  
    },  
    {  
        "custom\_mapping": {  
            "label": "Electricity generation",  
            "data\_version":"0.0"  
        },  
        "parameters": {  
            "energy": 200,  
            "energy\_unit": "kWh"  
        }  
    }  
\]

Response

## **Energy**

POST Electricity  
{{BASE\_URL}}/energy/v1/electricity

{  
    "year": 2023,  
    "region": "GB",  
    "amount": {  
        "energy": 5000,  
        "energy\_unit": "kWh"  
    },  
    "recs": {  
        "energy": 1000,  
        "energy\_unit": "kWh"  
    },  
    "components": \[  
        {  
            "amount": {  
                "energy": 1000,  
                "energy\_unit": "kWh"  
            },  
            "connection\_type": "grid",  
            "supplier": "british\_gas"  
        },  
        {  
            "amount": {  
                "energy": 1000,  
                "energy\_unit": "kWh"  
            },  
            "connection\_type": "direct",  
            "loss\_factor": 0.05,  
            "energy\_source": "natural\_gas"  
        },  
        {  
            "amount": {  
                "energy": 1000,  
                "energy\_unit": "kWh"  
            },  
            "connection\_type": "direct",  
            "energy\_source": "renewable"  
        }  
    \]  
}

Response

{

    "location": {

        "consumption": {

            "co2e": 1006.83593774,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": 999.389433962,

                "ch4": 0.116943396226,

                "n2o": 0.0145113207547

            }

        },

        "well\_to\_tank": {

            "co2e": 200.850943396,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "f0cd3fdd-533e-41d1-828d-fd4d103dc2ad"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": null,

                "ch4": null,

                "n2o": null

            }

        },

        "transmission\_and\_distribution": {

            "co2e": 74.0659762493,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Default transmission & distribution loss factor for direct electricity",

                    "source": "Climatiq",

                    "source\_dataset": null,

                    "year": null,

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid: T\&D losses",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": 73.4493005421,

                "ch4": 0.00941016253066,

                "n2o": 0.00123169547153

            }

        },

        "well\_to\_tank\_of\_transmission\_and\_distribution": {

            "co2e": 15.2403997247,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Default transmission & distribution loss factor for direct electricity",

                    "source": "Climatiq",

                    "source\_dataset": null,

                    "year": null,

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "f0cd3fdd-533e-41d1-828d-fd4d103dc2ad"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid: T\&D losses",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": null,

                "ch4": null,

                "n2o": null

            }

        }

    },

    "market": {

        "consumption": {

            "co2e": 889.649443453,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid \- residual mix",

                    "source": "AIB",

                    "source\_dataset": "European Residual Mix",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "3bf35117-1ad2-42ba-a403-c5fa92db0925"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid \- supplier British Gas",

                    "source": "Electricity Info",

                    "source\_dataset": "Fuel Mix of UK Domestic Electricity Suppliers",

                    "year": "2022",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "70889b28-cef0-4dce-9af4-25cce6a88eb3"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": 888.913884962,

                "ch4": null,

                "n2o": null

            }

        },

        "well\_to\_tank": {

            "co2e": 148.899700066,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_mixed\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Default well-to-tank ratio of electricity generation emissions",

                    "source": "Climatiq",

                    "source\_dataset": null,

                    "year": null,

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid \- residual mix",

                    "source": "AIB",

                    "source\_dataset": "European Residual Mix",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "3bf35117-1ad2-42ba-a403-c5fa92db0925"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid \- supplier British Gas",

                    "source": "Electricity Info",

                    "source\_dataset": "Fuel Mix of UK Domestic Electricity Suppliers",

                    "year": "2022",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "70889b28-cef0-4dce-9af4-25cce6a88eb3"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": null,

                "ch4": null,

                "n2o": null

            }

        },

        "transmission\_and\_distribution": {

            "co2e": 74.0659762493,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Default transmission & distribution loss factor for direct electricity",

                    "source": "Climatiq",

                    "source\_dataset": null,

                    "year": null,

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid: T\&D losses",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": 73.4493005421,

                "ch4": 0.00941016253066,

                "n2o": 0.00123169547153

            }

        },

        "well\_to\_tank\_of\_transmission\_and\_distribution": {

            "co2e": 15.2403997247,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for electricity generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": null,

                    "name": "Default transmission & distribution loss factor for direct electricity",

                    "source": "Climatiq",

                    "source\_dataset": null,

                    "year": null,

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "f0cd3fdd-533e-41d1-828d-fd4d103dc2ad"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Electricity supplied from grid: T\&D losses",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                    "year": "2023",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": null,

                "ch4": null,

                "n2o": null

            }

        }

    },

    "notices": \[

        {

            "severity": "info",

            "code": "recs\_subtracted\_market\_generation",

            "message": "Market generation components were subtracted for RECs"

        },

        {

            "severity": "warning",

            "code": "global\_default\_wtt\_used",

            "message": "Calculating market well to tank emissions using a global average proportion of generation emissions, due to absence of an applicable emissions factor. For more accurate market well to tank emissions, explicitly provide a fuel mix."

        }

    \]

}

POST Batch Electricity  
{{BASE\_URL}}/energy/v1/electricity/batch  
\[  
    {  
        "year": 2023,  
        "region": "GB",  
        "amount": {  
            "energy": 5000,  
            "energy\_unit": "kWh"  
        },  
        "recs": {  
            "energy": 1000,  
            "energy\_unit": "kWh"  
        },  
        "components": \[  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "connection\_type": "grid",  
                "supplier": "british\_gas"  
            },  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "connection\_type": "direct",  
                "loss\_factor": 0.05,  
                "energy\_source": "natural\_gas"  
            },  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "connection\_type": "direct",  
                "energy\_source": "renewable"  
            }  
        \]  
    },  
    {  
        "year": 2021,  
        "region": "GB",  
        "amount": {  
            "energy": 2000,  
            "energy\_unit": "kWh"  
        },  
        "recs": {  
            "energy": 3000,  
            "energy\_unit": "kWh"  
        },  
        "components": \[  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "connection\_type": "grid",  
                "supplier": "british\_gas"  
            }  
        \]  
    }  
\]

Response

{

    "results": \[

        {

            "location": {

                "consumption": {

                    "co2e": 1006.83593774,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 999.389433962,

                        "ch4": 0.116943396226,

                        "n2o": 0.0145113207547

                    }

                },

                "well\_to\_tank": {

                    "co2e": 200.850943396,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "f0cd3fdd-533e-41d1-828d-fd4d103dc2ad"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                },

                "transmission\_and\_distribution": {

                    "co2e": 74.0659762493,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": null,

                            "name": "Default transmission & distribution loss factor for direct electricity",

                            "source": "Climatiq",

                            "source\_dataset": null,

                            "year": null,

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid: T\&D losses",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 73.4493005421,

                        "ch4": 0.00941016253066,

                        "n2o": 0.00123169547153

                    }

                },

                "well\_to\_tank\_of\_transmission\_and\_distribution": {

                    "co2e": 15.2403997247,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": null,

                            "name": "Default transmission & distribution loss factor for direct electricity",

                            "source": "Climatiq",

                            "source\_dataset": null,

                            "year": null,

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "f0cd3fdd-533e-41d1-828d-fd4d103dc2ad"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid: T\&D losses",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                }

            },

            "market": {

                "consumption": {

                    "co2e": 889.649443453,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid \- residual mix",

                            "source": "AIB",

                            "source\_dataset": "European Residual Mix",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "3bf35117-1ad2-42ba-a403-c5fa92db0925"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid \- supplier British Gas",

                            "source": "Electricity Info",

                            "source\_dataset": "Fuel Mix of UK Domestic Electricity Suppliers",

                            "year": "2022",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "70889b28-cef0-4dce-9af4-25cce6a88eb3"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 888.913884962,

                        "ch4": null,

                        "n2o": null

                    }

                },

                "well\_to\_tank": {

                    "co2e": 148.899700066,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_mixed\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": null,

                            "name": "Default well-to-tank ratio of electricity generation emissions",

                            "source": "Climatiq",

                            "source\_dataset": null,

                            "year": null,

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid \- residual mix",

                            "source": "AIB",

                            "source\_dataset": "European Residual Mix",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "3bf35117-1ad2-42ba-a403-c5fa92db0925"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid \- supplier British Gas",

                            "source": "Electricity Info",

                            "source\_dataset": "Fuel Mix of UK Domestic Electricity Suppliers",

                            "year": "2022",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "70889b28-cef0-4dce-9af4-25cce6a88eb3"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                },

                "transmission\_and\_distribution": {

                    "co2e": 74.0659762493,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": null,

                            "name": "Default transmission & distribution loss factor for direct electricity",

                            "source": "Climatiq",

                            "source\_dataset": null,

                            "year": null,

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid: T\&D losses",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "14066219-ddb5-463a-b6d1-b5a277c5abe0"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 73.4493005421,

                        "ch4": 0.00941016253066,

                        "n2o": 0.00123169547153

                    }

                },

                "well\_to\_tank\_of\_transmission\_and\_distribution": {

                    "co2e": 15.2403997247,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for electricity generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": null,

                            "name": "Default transmission & distribution loss factor for direct electricity",

                            "source": "Climatiq",

                            "source\_dataset": null,

                            "year": null,

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "d53d2fff-6f3e-4a7d-aa78-e05b3a59ee57"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "f0cd3fdd-533e-41d1-828d-fd4d103dc2ad"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid: T\&D losses",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "54badec0-d6dc-4d6a-9a80-289059750e39"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                            "year": "2023",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "8248d37e-257b-44d5-a0bd-c4fbc0df1046"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                }

            },

            "notices": \[

                {

                    "severity": "info",

                    "code": "recs\_subtracted\_market\_generation",

                    "message": "Market generation components were subtracted for RECs"

                },

                {

                    "severity": "warning",

                    "code": "global\_default\_wtt\_used",

                    "message": "Calculating market well to tank emissions using a global average proportion of generation emissions, due to absence of an applicable emissions factor. For more accurate market well to tank emissions, explicitly provide a fuel mix."

                }

            \]

        },

        {

            "location": {

                "consumption": {

                    "co2e": 424.7388,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "2a267a78-9ec4-4b40-8bb5-c8a8bdf71edc"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 420.32,

                        "ch4": 0.064,

                        "n2o": 0.0092

                    }

                },

                "well\_to\_tank": {

                    "co2e": 110.58,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "05baba72-97c6-4aa8-a58f-71bb0547f4fc"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                },

                "transmission\_and\_distribution": {

                    "co2e": 37.586918,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "2a267a78-9ec4-4b40-8bb5-c8a8bdf71edc"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid: T\&D losses",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "6c195d14-2de1-4556-9869-21d3616bd078"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 37.1958798531,

                        "ch4": 0.00566362845118,

                        "n2o": 0.000814146589857

                    }

                },

                "well\_to\_tank\_of\_transmission\_and\_distribution": {

                    "co2e": 9.78570244431,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "05baba72-97c6-4aa8-a58f-71bb0547f4fc"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "2a267a78-9ec4-4b40-8bb5-c8a8bdf71edc"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Electricity supplied from grid: T\&D losses",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "6c195d14-2de1-4556-9869-21d3616bd078"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                }

            },

            "market": {

                "consumption": {

                    "co2e": 0.0,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[\],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 0.0,

                        "ch4": 0.0,

                        "n2o": 0.0

                    }

                },

                "well\_to\_tank": {

                    "co2e": 0.0,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[\],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 0.0,

                        "ch4": 0.0,

                        "n2o": 0.0

                    }

                },

                "transmission\_and\_distribution": {

                    "co2e": 0.0,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[\],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 0.0,

                        "ch4": 0.0,

                        "n2o": 0.0

                    }

                },

                "well\_to\_tank\_of\_transmission\_and\_distribution": {

                    "co2e": 0.0,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[\],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 0.0,

                        "ch4": 0.0,

                        "n2o": 0.0

                    }

                }

            },

            "notices": \[

                {

                    "severity": "info",

                    "code": "recs\_subtracted\_market\_generation",

                    "message": "Market generation components were subtracted for RECs"

                },

                {

                    "severity": "info",

                    "code": "recs\_subtracted\_market\_transmission\_and\_distribution",

                    "message": "Market transmission and distribution components were subtracted for RECs"

                },

                {

                    "severity": "warning",

                    "code": "global\_default\_wtt\_used",

                    "message": "Calculating market well to tank emissions using a global average proportion of generation emissions, due to absence of an applicable emissions factor. For more accurate market well to tank emissions, explicitly provide a fuel mix."

                }

            \]

        }

    \]

}

POST Heat and Steam  
{{BASE\_URL}}/energy/v1/heat  
{  
    "year": 2021,  
    "region": "DE",  
    "components": \[  
        {  
            "amount": {  
                "energy": 1000,  
                "energy\_unit": "kWh"  
            },  
            "loss\_factor": 0.06  
        },  
        {  
            "amount": {  
                "energy": 1000,  
                "energy\_unit": "kWh"  
            },  
            "loss\_factor": 0.1,  
            "energy\_source": "natural\_gas"  
        },  
        {  
            "amount": {  
                "energy": 1000,  
                "energy\_unit": "kWh"  
            },  
            "energy\_source": "renewable"  
        }  
    \]  
}

Response

{

    "estimates": {

        "consumption": {

            "co2e": 479.934263333,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for district heat generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "District heating",

                    "source": "UBA",

                    "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                    "year": "2021",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                    "year": "2021",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "1e1ffef5-6478-4356-a13b-fa0f66d962d1"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": 475.940888889,

                "ch4": 0.0844444444444,

                "n2o": 0.00541

            }

        },

        "well\_to\_tank": {

            "co2e": 78.891,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for district heat generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "District heating",

                    "source": "UBA",

                    "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                    "year": "2021",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "District heating",

                    "source": "UBA",

                    "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                    "year": "2021",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "21035a1d-f1df-452b-b673-c69895065b1c"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                    "year": "2021",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "aa9240f8-ca36-4405-bed9-083678faa694"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": null,

                "ch4": null,

                "n2o": null

            }

        },

        "transmission\_and\_distribution": {

            "co2e": 41.3703507723,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for district heat generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "District heating",

                    "source": "UBA",

                    "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                    "year": "2021",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                    "year": "2021",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "1e1ffef5-6478-4356-a13b-fa0f66d962d1"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": 41.0926283163,

                "ch4": 0.00597846073023,

                "n2o": 0.000364704491726

            }

        },

        "well\_to\_tank\_of\_transmission\_and\_distribution": {

            "co2e": 6.86065484634,

            "co2e\_unit": "kg",

            "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

            "source\_trail": \[

                {

                    "data\_category": null,

                    "name": "Combustion efficiency of natural gas for district heat generation",

                    "source": "CBAM",

                    "source\_dataset": null,

                    "year": null,

                    "region": "EU",

                    "region\_name": "European Union",

                    "id": null

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "District heating",

                    "source": "UBA",

                    "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                    "year": "2021",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "District heating",

                    "source": "UBA",

                    "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                    "year": "2021",

                    "region": "DE",

                    "region\_name": "Germany",

                    "id": "21035a1d-f1df-452b-b673-c69895065b1c"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Natural gas \- 100% mineral blend (net CV)",

                    "source": "BEIS",

                    "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                    "year": "2021",

                    "region": "GB",

                    "region\_name": "United Kingdom",

                    "id": "aa9240f8-ca36-4405-bed9-083678faa694"

                },

                {

                    "data\_category": "emission\_factor",

                    "name": "Renewables",

                    "source": "Climatiq",

                    "source\_dataset": "Climatiq",

                    "year": "2022",

                    "region": "GLOBAL",

                    "region\_name": "Global",

                    "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                }

            \],

            "co2\_biogenic": null,

            "constituent\_gases": {

                "co2": null,

                "ch4": null,

                "n2o": null

            }

        }

    }

}

POST Batch Heat and Steam  
{{BASE\_URL}}/energy/v1/heat/batch

\[  
    {  
        "year": 2021,  
        "region": "DE",  
        "components": \[  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "loss\_factor": 0.06  
            },  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "loss\_factor": 0.1,  
                "energy\_source": "natural\_gas"  
            },  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "energy\_source": "renewable"  
            }  
        \]  
    },  
    {  
        "year": 2021,  
        "region": "DE",  
        "components": \[  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "loss\_factor": 0.06  
            },  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "loss\_factor": 0.1,  
                "energy\_source": "natural\_gas"  
            },  
            {  
                "amount": {  
                    "energy": 1000,  
                    "energy\_unit": "kWh"  
                },  
                "energy\_source": "renewable"  
            }  
        \]  
    }  
\]

Response

{

    "results": \[

        {

            "estimates": {

                "consumption": {

                    "co2e": 479.934263333,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "1e1ffef5-6478-4356-a13b-fa0f66d962d1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 475.940888889,

                        "ch4": 0.0844444444444,

                        "n2o": 0.00541

                    }

                },

                "well\_to\_tank": {

                    "co2e": 78.891,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "21035a1d-f1df-452b-b673-c69895065b1c"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "aa9240f8-ca36-4405-bed9-083678faa694"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                },

                "transmission\_and\_distribution": {

                    "co2e": 41.3703507723,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "1e1ffef5-6478-4356-a13b-fa0f66d962d1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 41.0926283163,

                        "ch4": 0.00597846073023,

                        "n2o": 0.000364704491726

                    }

                },

                "well\_to\_tank\_of\_transmission\_and\_distribution": {

                    "co2e": 6.86065484634,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "21035a1d-f1df-452b-b673-c69895065b1c"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "aa9240f8-ca36-4405-bed9-083678faa694"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                }

            }

        },

        {

            "estimates": {

                "consumption": {

                    "co2e": 479.934263333,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "1e1ffef5-6478-4356-a13b-fa0f66d962d1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 475.940888889,

                        "ch4": 0.0844444444444,

                        "n2o": 0.00541

                    }

                },

                "well\_to\_tank": {

                    "co2e": 78.891,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "21035a1d-f1df-452b-b673-c69895065b1c"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "aa9240f8-ca36-4405-bed9-083678faa694"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                },

                "transmission\_and\_distribution": {

                    "co2e": 41.3703507723,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar6\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "1e1ffef5-6478-4356-a13b-fa0f66d962d1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "4f80b533-b3ef-43d3-b51b-fddcd3e4b754"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": 41.0926283163,

                        "ch4": 0.00597846073023,

                        "n2o": 0.000364704491726

                    }

                },

                "well\_to\_tank\_of\_transmission\_and\_distribution": {

                    "co2e": 6.86065484634,

                    "co2e\_unit": "kg",

                    "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                    "source\_trail": \[

                        {

                            "data\_category": null,

                            "name": "Combustion efficiency of natural gas for district heat generation",

                            "source": "CBAM",

                            "source\_dataset": null,

                            "year": null,

                            "region": "EU",

                            "region\_name": "European Union",

                            "id": null

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "1e66f532-ec59-4f23-9606-0c63d4add4a1"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "District heating",

                            "source": "UBA",

                            "source\_dataset": "Emissionsbilanz erneuerbarer Energietraeger",

                            "year": "2021",

                            "region": "DE",

                            "region\_name": "Germany",

                            "id": "21035a1d-f1df-452b-b673-c69895065b1c"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Natural gas \- 100% mineral blend (net CV)",

                            "source": "BEIS",

                            "source\_dataset": "Greenhouse gas reporting: conversion factors 2021",

                            "year": "2021",

                            "region": "GB",

                            "region\_name": "United Kingdom",

                            "id": "aa9240f8-ca36-4405-bed9-083678faa694"

                        },

                        {

                            "data\_category": "emission\_factor",

                            "name": "Renewables",

                            "source": "Climatiq",

                            "source\_dataset": "Climatiq",

                            "year": "2022",

                            "region": "GLOBAL",

                            "region\_name": "Global",

                            "id": "775f78bb-3d1e-499b-a95f-3fbbf4ba12e9"

                        }

                    \],

                    "co2\_biogenic": null,

                    "constituent\_gases": {

                        "co2": null,

                        "ch4": null,

                        "n2o": null

                    }

                }

            }

        }

    \]

}

POST Fuel  
{{BASE\_URL}}/energy/v1/fuel  
{  
    "fuel\_type": "biodiesel\_bio\_100",  
    "amount": {  
        "volume": 5000,  
        "volume\_unit": "l"  
    },  
    "region": "GB",  
    "year": 2023  
}

Response

{

    "combustion": {

        "co2e": 837.55,

        "co2e\_unit": "kg",

        "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

        "source\_trail": \[

            {

                "data\_category": "emission\_factor",

                "name": "Off road biodiesel",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "414c53d5-8844-4250-8b4d-09a8a1133535"

            },

            {

                "data\_category": "emission\_factor",

                "name": "Off road biodiesel",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "c1c8c8f9-38f4-4057-a245-49e9d8c93798"

            }

        \],

        "co2\_biogenic": 11950.0,

        "constituent\_gases": {

            "co2": null,

            "ch4": null,

            "n2o": null

        }

    },

    "well\_to\_tank": {

        "co2e": 2237.95,

        "co2e\_unit": "kg",

        "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

        "source\_trail": \[

            {

                "data\_category": "emission\_factor",

                "name": "Off road biodiesel",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "b4d508d5-d6c5-48e0-a86d-3cca2b268657"

            }

        \],

        "co2\_biogenic": null,

        "constituent\_gases": {

            "co2": null,

            "ch4": null,

            "n2o": null

        }

    },

    "notices": \[\]

}

POST Batch Fuel  
{{BASE\_URL}}/energy/v1/fuel/batch  
\[  
    {  
        "fuel\_type": "biodiesel\_bio\_100",  
        "amount": {  
            "volume": 5000,  
            "volume\_unit": "l"  
        },  
        "region": "GB",  
        "year": 2023  
    },  
    {  
        "fuel\_type": "biodiesel\_bio\_100",  
        "amount": {  
            "volume": 3000,  
            "volume\_unit": "l"  
        },  
        "region": "GB",  
        "year": 2021  
    }  
\]

Response

{

    "results": \[

        {

            "combustion": {

                "co2e": 837.55,

                "co2e\_unit": "kg",

                "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

                "source\_trail": \[

                    {

                        "data\_category": "emission\_factor",

                        "name": "Off road biodiesel",

                        "source": "BEIS",

                        "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                        "year": "2023",

                        "region": "GB",

                        "region\_name": "United Kingdom",

                        "id": "414c53d5-8844-4250-8b4d-09a8a1133535"

                    },

                    {

                        "data\_category": "emission\_factor",

                        "name": "Off road biodiesel",

                        "source": "BEIS",

                        "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                        "year": "2023",

                        "region": "GB",

                        "region\_name": "United Kingdom",

                        "id": "c1c8c8f9-38f4-4057-a245-49e9d8c93798"

                    }

                \],

                "co2\_biogenic": 11950.0,

                "constituent\_gases": {

                    "co2": null,

                    "ch4": null,

                    "n2o": null

                }

            },

            "well\_to\_tank": {

                "co2e": 2237.95,

                "co2e\_unit": "kg",

                "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

                "source\_trail": \[

                    {

                        "data\_category": "emission\_factor",

                        "name": "Off road biodiesel",

                        "source": "BEIS",

                        "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                        "year": "2023",

                        "region": "GB",

                        "region\_name": "United Kingdom",

                        "id": "b4d508d5-d6c5-48e0-a86d-3cca2b268657"

                    }

                \],

                "co2\_biogenic": null,

                "constituent\_gases": {

                    "co2": null,

                    "ch4": null,

                    "n2o": null

                }

            },

            "notices": \[\]

        },

        {

            "combustion": {

                "co2e": 502.53,

                "co2e\_unit": "kg",

                "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                "source\_trail": \[

                    {

                        "data\_category": "emission\_factor",

                        "name": "Off road biodiesel",

                        "source": "BEIS",

                        "source\_dataset": "Greenhouse gas reporting: conversion factors 2022",

                        "year": "2022",

                        "region": "GB",

                        "region\_name": "United Kingdom",

                        "id": "89f6c742-a86c-4943-9408-a67b2c89d5c5"

                    },

                    {

                        "data\_category": "emission\_factor",

                        "name": "Off road biodiesel",

                        "source": "BEIS",

                        "source\_dataset": "Greenhouse gas reporting: conversion factors 2022",

                        "year": "2022",

                        "region": "GB",

                        "region\_name": "United Kingdom",

                        "id": "96abeebf-08c0-4393-abf9-b0ce196cb0ae"

                    }

                \],

                "co2\_biogenic": 7080.0,

                "constituent\_gases": {

                    "co2": null,

                    "ch4": null,

                    "n2o": null

                }

            },

            "well\_to\_tank": {

                "co2e": 1089.99,

                "co2e\_unit": "kg",

                "co2e\_calculation\_method": "ipcc\_ar4\_gwp100",

                "source\_trail": \[

                    {

                        "data\_category": "emission\_factor",

                        "name": "Off road biodiesel",

                        "source": "BEIS",

                        "source\_dataset": "Greenhouse gas reporting: conversion factors 2022",

                        "year": "2022",

                        "region": "GB",

                        "region\_name": "United Kingdom",

                        "id": "dc47bc76-94d4-4477-98ee-1f7c35634908"

                    }

                \],

                "co2\_biogenic": null,

                "constituent\_gases": {

                    "co2": null,

                    "ch4": null,

                    "n2o": null

                }

            },

            "notices": \[\]

        }

    \]

}

## **Travel Flights**

Calculate total estimated emissions produced by travel:

* Distance-based  
* Spend-based  
* Hotel nights

POST Distance-based method

{{PREVIEW\_V1\_BASE\_URL}}/travel/v1-preview1/distance

{

    "origin": {

        "locode": "DE-HAM"

    },

    "destination": {

        "query": "Berlin"

    },

    "travel\_mode": "car",

    "car\_details": {

        "car\_type": "plugin\_hybrid"

   }

}

Response

{

    "co2e": 45.4109977279,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_mixed\_gwp100",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Electricity supplied from grid \- production mix",

            "source": "AIB",

            "source\_dataset": "European Residual Mix",

            "year": "2022",

            "region": "DE",

            "region\_name": "Germany",

            "id": "93fd4e16-4dbc-4d42-a2b3-3295441f3805"

        },

        {

            "data\_category": "emission\_factor",

            "name": "Petrol (100% mineral petrol)",

            "source": "BEIS",

            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

            "year": "2023",

            "region": "GB",

            "region\_name": "United Kingdom",

            "id": "4c4e7091-620d-47ca-9c95-316ffa49b9a1"

        },

        {

            "data\_category": "emission\_factor",

            "name": "Petrol (100% mineral petrol)",

            "source": "BEIS",

            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

            "year": "2023",

            "region": "GB",

            "region\_name": "United Kingdom",

            "id": "ba362f0a-f84a-469d-9ee0-3c0dae69ab57"

        }

    \],

    "distance\_km": 306.782,

    "origin": {

        "name": "Hamburg",

        "confidence\_score": null

    },

    "destination": {

        "name": "Berlin, Germany",

        "confidence\_score": 1.0

    },

    "direct\_emissions": {

        "co2e": 35.1378742574,

        "co2e\_unit": "kg",

        "source\_trail": \[

            {

                "data\_category": "emission\_factor",

                "name": "Electricity supplied from grid \- production mix",

                "source": "AIB",

                "source\_dataset": "European Residual Mix",

                "year": "2022",

                "region": "DE",

                "region\_name": "Germany",

                "id": "93fd4e16-4dbc-4d42-a2b3-3295441f3805"

            },

            {

                "data\_category": "emission\_factor",

                "name": "Petrol (100% mineral petrol)",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "ba362f0a-f84a-469d-9ee0-3c0dae69ab57"

            }

        \]

    },

    "indirect\_emissions": {

        "co2e": 10.2731234704,

        "co2e\_unit": "kg",

        "source\_trail": \[

            {

                "data\_category": "emission\_factor",

                "name": "Electricity supplied from grid \- production mix",

                "source": "AIB",

                "source\_dataset": "European Residual Mix",

                "year": "2022",

                "region": "DE",

                "region\_name": "Germany",

                "id": "93fd4e16-4dbc-4d42-a2b3-3295441f3805"

            },

            {

                "data\_category": "emission\_factor",

                "name": "Petrol (100% mineral petrol)",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "4c4e7091-620d-47ca-9c95-316ffa49b9a1"

            }

        \]

    },

    "notices": \[\]

}

POST Distance-based with location query

{

    "origin": {

        "query": "Grindelhof 28-30, Hamburg",

        "country": "DE",

        "postal\_code":"20146"

    },

    "destination": {

        "query": "Berlin"

    },

    "travel\_mode": "car",

    "car\_details": {

        "car\_type": "plugin\_hybrid"

   }

}

Response

{

    "co2e": 43.3173509303,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_mixed\_gwp100",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Electricity supplied from grid \- production mix",

            "source": "AIB",

            "source\_dataset": "European Residual Mix",

            "year": "2022",

            "region": "DE",

            "region\_name": "Germany",

            "id": "93fd4e16-4dbc-4d42-a2b3-3295441f3805"

        },

        {

            "data\_category": "emission\_factor",

            "name": "Petrol (100% mineral petrol)",

            "source": "BEIS",

            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

            "year": "2023",

            "region": "GB",

            "region\_name": "United Kingdom",

            "id": "4c4e7091-620d-47ca-9c95-316ffa49b9a1"

        },

        {

            "data\_category": "emission\_factor",

            "name": "Petrol (100% mineral petrol)",

            "source": "BEIS",

            "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

            "year": "2023",

            "region": "GB",

            "region\_name": "United Kingdom",

            "id": "ba362f0a-f84a-469d-9ee0-3c0dae69ab57"

        }

    \],

    "distance\_km": 292.638,

    "origin": {

        "name": "Grindelhof 30, 20146 Hamburg, Germany",

        "confidence\_score": 0.92

    },

    "destination": {

        "name": "Berlin, Germany",

        "confidence\_score": 1.0

    },

    "direct\_emissions": {

        "co2e": 33.5178636522,

        "co2e\_unit": "kg",

        "source\_trail": \[

            {

                "data\_category": "emission\_factor",

                "name": "Electricity supplied from grid \- production mix",

                "source": "AIB",

                "source\_dataset": "European Residual Mix",

                "year": "2022",

                "region": "DE",

                "region\_name": "Germany",

                "id": "93fd4e16-4dbc-4d42-a2b3-3295441f3805"

            },

            {

                "data\_category": "emission\_factor",

                "name": "Petrol (100% mineral petrol)",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "ba362f0a-f84a-469d-9ee0-3c0dae69ab57"

            }

        \]

    },

    "indirect\_emissions": {

        "co2e": 9.79948727808,

        "co2e\_unit": "kg",

        "source\_trail": \[

            {

                "data\_category": "emission\_factor",

                "name": "Electricity supplied from grid \- production mix",

                "source": "AIB",

                "source\_dataset": "European Residual Mix",

                "year": "2022",

                "region": "DE",

                "region\_name": "Germany",

                "id": "93fd4e16-4dbc-4d42-a2b3-3295441f3805"

            },

            {

                "data\_category": "emission\_factor",

                "name": "Petrol (100% mineral petrol)",

                "source": "BEIS",

                "source\_dataset": "Greenhouse gas reporting: conversion factors 2023",

                "year": "2023",

                "region": "GB",

                "region\_name": "United Kingdom",

                "id": "4c4e7091-620d-47ca-9c95-316ffa49b9a1"

            }

        \]

    },

    "notices": \[\]

}

POST Spend-based method

{{PREVIEW\_V1\_BASE\_URL}}/travel/v1-preview1/spend

{

    "spend\_type": "air",

    "money": 100,

    "money\_unit": "gbp",

    "spend\_location": {

        "locode": "GB-LON"

    },

    "spend\_year": 2022

}

Response

{

    "co2e": 119.195972889,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

    "source\_trail": \[

        {

            "data\_category": null,

            "name": "Country-specific inflation rates",

            "source": "World Bank",

            "source\_dataset": null,

            "year": null,

            "region": "GB",

            "region\_name": "United Kingdom",

            "id": null

        },

        {

            "data\_category": "emission\_factor",

            "name": "Air transport services",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "GB",

            "region\_name": "United Kingdom",

            "id": "99c2d920-e6ef-41cf-a9c3-97b8501e42ea"

        }

    \],

    "spend\_location": {

        "name": "London, LND, GB",

        "confidence\_score": null

    },

    "notices": \[\]

}

POST Spend-based with IATA code

{{PREVIEW\_V1\_BASE\_URL}}/travel/v1-preview1/spend

{

    "spend\_type": "air",

    "money": 100,

    "money\_unit": "eur",

    "spend\_location": {

        "iata": "AGP"

    },

    "spend\_year": 2022

}

Response

{

    "co2e": 117.743507485,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

    "source\_trail": \[

        {

            "data\_category": null,

            "name": "Industry-specific inflation rates",

            "source": "EUROSTAT",

            "source\_dataset": null,

            "year": null,

            "region": "ES",

            "region\_name": "Spain",

            "id": null

        },

        {

            "data\_category": "emission\_factor",

            "name": "Air transport services",

            "source": "EXIOBASE",

            "source\_dataset": "EXIOBASE 3",

            "year": "2019",

            "region": "ES",

            "region\_name": "Spain",

            "id": "dddaa7a3-d9f5-421f-be12-3b6f962a1f62"

        }

    \],

    "spend\_location": {

        "name": "Spain",

        "confidence\_score": null

    },

    "notices": \[\]

}

POST Hotels

{{PREVIEW\_V1\_BASE\_URL}}/travel/v1-preview1/hotel

{

    "hotel\_nights": 5,

    "location": {

        "query": "Lisbon"

    },

    "year": 2024

}

Response

{

    "co2e": 95.0,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Hotel stay",

            "source": "BEIS",

            "source\_dataset": "Greenhouse gas reporting: conversion factors 2024",

            "year": "2024",

            "region": "PT",

            "region\_name": "Portugal",

            "id": "30c62f32-4c5d-4b53-ab55-8c5b5d45c4e3"

        }

    \],

    "location": {

        "name": "Portugal",

        "confidence\_score": 1.0

    },

    "notices": \[\]

}

POST Hotels with coordinates

{{PREVIEW\_V1\_BASE\_URL}}/travel/v1-preview1/hotel{

    "hotel\_nights": 5,

    "location": {

        "latitude": 53.56849,

        "longitude": 9.98335,

        "country":"DE"

    },

    "year": 2024

}

Response

{

    "co2e": 66.0,

    "co2e\_unit": "kg",

    "co2e\_calculation\_method": "ipcc\_ar5\_gwp100",

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Hotel stay",

            "source": "BEIS",

            "source\_dataset": "Greenhouse gas reporting: conversion factors 2024",

            "year": "2024",

            "region": "DE",

            "region\_name": "Germany",

            "id": "dd5fbb33-7ba9-4add-9d0a-d053d37841dd"

        }

    \],

    "location": {

        "name": "Germany",

        "confidence\_score": null

    },

    "notices": \[\]

}

## **Autopilot**

Autopilot is an AI-powered calculation endpoint designed to automate spend- and activity-based emission estimates. It uses a proprietary natural language processing (NLP) model paired with Climatiq’s scientific expertise to streamline complex emission calculations, making carbon insights accessible to non-experts.

POST Suggest  
{{PREVIEW\_V1\_BASE\_URL}}/autopilot/v1-preview3/suggest  
{  
    "suggest": {  
        "domain": "general",  
        "text": "Cement"  
    },  
    "max\_suggestions": 2  
}

Response

{

    "results": \[

        {

            "suggestion\_id": "gq2gcyrsgrrdqljsgjrtkljumqytsljygy3toljrgqyday3fgezggzrwmq-mvrgimztgyytaljxmjrdkljuge4wcljyge4dmljymq4donzqgm3tkm3cmy",

            "emission\_factor": {

                "sector": "Materials and Manufacturing",

                "category": "Building Materials",

                "name": "Cement",

                "unit\_type": "Money",

                "unit": "kg/usd",

                "source": "EPA",

                "source\_dataset": "Supply Chain Greenhouse Gas Emission Factors v1.3",

                "year": 2022,

                "year\_released": 2024,

                "region": "US",

                "region\_name": "United States of America (the)",

                "description": "Emission intensity of supply chain (with margins i.e. cradle to shelf) in US dollars at 2022 prices. This factor is representative of the described goods or services category as defined by the 2017 version of the North American Industry Classification System (NAICS). NAICS Code: 327310\. Refer to the source for the source-specific data quality assessment. Retrieved from Supply Chain Factors Dataset v1.3.",

                "source\_link": "https://cfpub.epa.gov/si/si\_public\_record\_Report.cfm?dirEntryId=349324\&Lab=CESER",

                "source\_lca\_activity": "cradle\_to\_shelf",

                "data\_quality\_flags": \[\],

                "access\_type": "public"

            },

            "suggestion\_details": {

                "similarity\_score": 1.0,

                "confidence": "high"

            }

        },

        {

            "suggestion\_id": "mnrtmytgmzrwiljtga4gmljumjqtsllbmuzggljwgvrwcytbmiydkmrzga-mvrgimztgyytaljxmjrdkljuge4wcljyge4dmljymq4donzqgm3tkm3cmy",

            "emission\_factor": {

                "sector": "Materials and Manufacturing",

                "category": "Building Materials",

                "name": "Cement \- unspecified (market group for)",

                "unit\_type": "Weight",

                "unit": "kg/kg",

                "source": "ecoinvent",

                "source\_dataset": "Cut-off Cumulative LCIA v3.11",

                "year": 2019,

                "year\_released": 2024,

                "region": "GLOBAL",

                "region\_name": "Global",

                "description": "The activity generating the emissions is market group for cement, unspecified. The reference product is cement, unspecified. The product cement, unspecified represents a weighted average of all types of cement in a generic market for cement based on their production volumes. The reference product amount is 1\. The cut-off classification is allocatable product. The activity type is ordinary market group. Please refer to the ecoinvent documentation here for full details: https://ecoquery.ecoinvent.org/3.11/cutoff/dataset/20218/documentation.",

                "source\_link": "https://ecoquery.ecoinvent.org/3.11/cutoff/search",

                "source\_lca\_activity": "unknown",

                "data\_quality\_flags": \[\],

                "access\_type": "premium"

            },

            "suggestion\_details": {

                "similarity\_score": 0.91,

                "confidence": "high"

            }

        }

    \]

}

POST Estimate  
{{PREVIEW\_V1\_BASE\_URL}}/autopilot/v1-preview3/suggest/estimate  
{  
    "suggestion\_id": "giytkntbha4weljxmjstqljugqydkllbmfrdsljqga2ggylemu4wmzdfme-mvsdcolbmizgiljtmy2daljugiygillbmztgeljrgnsdomrzgnrtgodbgm",  
    "parameters": {  
        "money": 100,  
        "money\_unit": "usd"  
    }  
}

Response

{

    "estimate": {

        "co2e": 392.4,

        "co2e\_unit": "kg",

        "co2e\_calculation\_method": "ar5",

        "co2e\_calculation\_origin": "source",

        "emission\_factor": {

            "name": "Cement",

            "activity\_id": "building\_materials-type\_cement",

            "id": "2156a89b-7be8-4405-aab9-004cade9fdea",

            "access\_type": "public",

            "source": "EPA",

            "source\_dataset": "Supply Chain Greenhouse Gas Emission Factors v1.3",

            "year": 2022,

            "region": "US",

            "category": "Building Materials",

            "source\_lca\_activity": "cradle\_to\_shelf",

            "data\_quality\_flags": \[\]

        },

        "constituent\_gases": {

            "co2e\_total": 392.4,

            "co2e\_other": null,

            "co2": 386.0,

            "ch4": 0.198,

            "n2o": 0.00355

        },

        "activity\_data": {

            "activity\_value": 100.0,

            "activity\_unit": "usd"

        },

        "audit\_trail": "enabled"

    },

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Cement",

            "source": "EPA",

            "source\_dataset": "Supply Chain Greenhouse Gas Emission Factors v1.3",

            "year": "2022",

            "region": "US",

            "region\_name": "United States of America (the)",

            "id": "2156a89b-7be8-4405-aab9-004cade9fdea"

        }

    \]

}

POST One-Shot Estimate  
{{PREVIEW\_V1\_BASE\_URL}}/autopilot/v1-preview3/estimate  
{  
    "domain": "general",  
    "text": "Steel",  
    "parameters": {  
        "money": 100,  
        "money\_unit": "usd"  
    }  
}

Response

{

    "estimate": {

        "co2e": 47.0,

        "co2e\_unit": "kg",

        "co2e\_calculation\_method": "ar4",

        "co2e\_calculation\_origin": "climatiq",

        "emission\_factor": {

            "name": "Cast iron and steel",

            "activity\_id": "metals-type\_cast\_iron\_steel",

            "id": "15e75a68-b485-494b-8cbc-398d417207a7",

            "access\_type": "public",

            "source": "EPA",

            "source\_dataset": "Supply Chain Factors Dataset (commodities)",

            "year": 2018,

            "region": "US",

            "category": "Metals",

            "source\_lca\_activity": "cradle\_to\_shelf",

            "data\_quality\_flags": \[\]

        },

        "constituent\_gases": {

            "co2e\_total": null,

            "co2e\_other": 0.7,

            "co2": 41.3,

            "ch4": 0.2,

            "n2o": 0.0

        },

        "activity\_data": {

            "activity\_value": 100.0,

            "activity\_unit": "usd"

        },

        "audit\_trail": "enabled"

    },

    "calculation\_details": {

        "similarity\_score": 0.87,

        "confidence": "high"

    },

    "source\_trail": \[

        {

            "data\_category": "emission\_factor",

            "name": "Cast iron and steel",

            "source": "EPA",

            "source\_dataset": "Supply Chain Factors Dataset (commodities)",

            "year": "2018",

            "region": "US",

            "region\_name": "United States of America (the)",

            "id": "15e75a68-b485-494b-8cbc-398d417207a7"

        }

    \]

}

