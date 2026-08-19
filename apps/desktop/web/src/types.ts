export type NodeMetrics={node_id:string;boot_id:string;observed_at:string;logical_cpus:number;load_1m:number;mem_total_bytes:number;mem_available_bytes:number;disk_total_bytes?:number;disk_available_bytes?:number;active_child_processes:number};
export type HumanAction={action_id:string;status:string;action_type:string;title:string;instructions:Record<string,unknown>;product_id?:string;factory_run_id?:string;work_node_id?:string;estimated_cost_usd?:number;requested_at:string;request_payload_hash:string};
export type Product={product_id:string;name:string;slug:string;product_type:string;status:string;factory_id?:string;factory_version?:string;build_run_id?:string;updated_at?:string};
export type Factory={factory_id:string;version:string;kind:string;name:string;phases:string[];mandatory_teams:string[];default_budget_usd:number};
export type ContextUsage={used:number;max:number;exact:boolean;buckets:Record<string,number>};
