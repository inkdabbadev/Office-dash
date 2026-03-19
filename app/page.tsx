"use client"

import { useEffect , useState } from "react";

type Row = {
  id: number;
  channel_name: string;
  followers: number;
  posts: number;
  img_url: string;
  profile_url?: string;
  scraped_at?: string;
};

export default function Home() {

  const [rows , setRows] = useState<Row[]>([]);

  useEffect(() => {
    async function fetchRows() {
      const res = await fetch("/api");
      const json = await res.json();
      setRows(json.data || []);
      
    }

    fetchRows();

  },[]);


  const maincont = ""
  return (
    <div className={` h-screen w-screen flex flex-col py-20 justify-center`}>
      <div className={`flex flex-row  f-fit justify-center gap-[3%]`}>
        {rows.slice(0,2).map((row) => (

          <div key={row.id} className={"relative h-full w-[30%]  bg-green-300 flex flex-col items-center rounded-xl gap-3 pb-5 px-5"}>
          
          
                    {/* image container */}
                    <div  className={`absolute bg-red-300/40 h-20 w-20 rounded-full -top-10 flex justify-center items-center left-auto `}>
                      <img src={row.img_url} className={`w-[75%]`} alt="" />
                    </div>
          

                    <h1 className={'mt-12 text-center font-bold'}>{row.channel_name} </h1>
                    <div className=" h-full flex flex-col justify-end">
                      
                    <p className={' text-center text-xs font-bold'}>Followers : {row.followers}</p>
                      <p className={' text-center text-xs font-bold'}>Posts : {row.posts}</p>
                    </div>

        </div>
        ))}
          
        
        

      </div>
      <div className="h-50 w-50  h-fit  w-full flex gap-3 flex-wrap justify-center p-5">

        {rows.slice(2).map((row) => (
            <div key={row.id}  className="relative rounded h-15 w-70 bg-green-400 ">
                          <div  className={`absolute  h-10 w-10 rounded-full top-2.5 left-2.5  flex justify-center items-center  `}>
                              <img src={row.img_url} className={``} alt="" />
                            </div>

                    <div className="ml-15  h-full flex  pt-1 pb-2 justify-between flex-col">
                      <h1 className="font-bold text-center ">{row.channel_name}</h1>
                      <p className="font-bold text-xs text-center">Followers : {row.followers} Posts : {row.posts}</p>

                    </div>
            </div>

        ))}

        
        
      </div>
    </div>
  );
}
