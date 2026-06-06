import {
    createProject
}
from "../services/project.service.js";

const form=
    document.getElementById(
        "projectForm"
    );

form?.addEventListener(
    "submit",
    async(event)=>{

        event.preventDefault();

        const payload={

            company_name:
                document.getElementById(
                    "companyName"
                ).value,

            name:
                document.getElementById(
                    "projectName"
                ).value,

            location:
                document.getElementById(
                    "location"
                ).value,

            project_capacity_mw:Number(
                document.getElementById(
                    "capacity"
                ).value
            ),

            turbine_model:
                document.getElementById(
                    "turbineModel"
                ).value,

            rated_power_kw:Number(
                document.getElementById(
                    "ratedPower"
                ).value
            ),

            description:
                document.getElementById(
                    "description"
                ).value
        };

        try{

            await createProject(
                payload
            );

            window.location.reload();
        }
        catch(error){

            alert(
                error.message
            );
        }
    }
);