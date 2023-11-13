classdef UObj
    properties
        V % value
        U % uncertainty
        P % uncertainty percentage
    end
    methods
        function uo = UObj(value, uncert)
            uo.V = value;
            uo.U = uncert;
            uo.P = uncert/value;
        end
        function obj = mul(obj, c)
            obj.V = obj.V * c;
            obj.U = abs(obj.U * c);
        end
        function obj = add(obj, c)
            obj.V = obj.V + c;
            obj.P = abs(obj.U / obj.V);
        end
        function obj = pwr(obj, c)
            obj.V = obj.V ^ c;
            obj.P = abs(obj.P * c);
            obj.U = abs(obj.P * obj.V);
        end
        function obj = u_mul(obj, m_obj)
            obj.V = obj.V * m_obj.V;
            obj.P = rssq([obj.P m_obj.P]);
            obj.U = abs(obj.P * obj.V);
        end
        function obj = u_div(obj, d_obj)
            obj.V = obj.V / d_obj.V;
            obj.P = rssq([obj.P d_obj.P]);
            obj.U = abs(obj.P * obj.V);
        end
        function obj = u_add(obj, a_obj)
            obj.V = obj.V + a_obj.V;
            obj.U = rssq([obj.U a_obj.U]);
            obj.P = abs(obj.U / obj.V);
        end
        function obj = u_sub(obj, s_obj)
            obj.V = obj.V - s_obj.V;
            obj.U = rssq([obj.U s_obj.U]);
            obj.P = abs(obj.U / obj.V);
        end
    end
end